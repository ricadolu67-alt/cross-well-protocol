#!/usr/bin/env python3
"""Validate the CROSS-WELL draft or frozen protocol package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required for protocol validation. Install it in the frozen "
        "environment and record the version in parameter_register.csv."
    ) from exc


PLACEHOLDER = "TO_BE_FROZEN"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_FILES = [
    "README.md",
    "01_deployment_claim.yaml",
    "02_candidate_acquisition_plan.yaml",
    "03_unit_registry.csv",
    "04_dependence_rules.yaml",
    "05_measurement_semantic_contract.csv",
    "05a_ROP_measurement_semantic_freeze_record.md",
    "05b_measurement_alignment_sampling_contract.yaml",
    "06_label_blinded_qualification.yaml",
    "07_falsification_diagnostics.yaml",
    "08_model_baseline_manifest.json",
    "09_loss_and_estimands.yaml",
    "10_uncertainty_plan.yaml",
    "11_confirmatory_cohort_manifest.csv",
    "12_outcome_lock_and_custody.yaml",
    "13_output_table_shells/README.md",
    "13_output_table_shells/01_candidate_flow.csv",
    "13_output_table_shells/02_family_metrics.csv",
    "13_output_table_shells/03_field_effects.csv",
    "13_output_table_shells/04_basin_context_summary.csv",
    "13_output_table_shells/05_leave_one_field_out.csv",
    "13_output_table_shells/06_leave_one_basin_out.csv",
    "13_output_table_shells/07_falsification_diagnostics.csv",
    "13_output_table_shells/08_uncertainty_summary.csv",
    "13_output_table_shells/09_claim_boundary_output.csv",
    "13_output_table_shells/10_execution_trace.csv",
    "14_claim_wording_matrix.md",
    "15_protocol_deviation_log.csv",
    "16_freeze_manifest.json",
    "parameter_register.csv",
    "v1.0_freeze_checklist.csv",
    "schemas/SCHEMA.md",
    "scripts/validate_protocol.py",
    "scripts/audit_source_sampling.py",
    "scripts/build_frozen_model_bundle.py",
    "scripts/build_measurement_semantic_contract.py",
    "scripts/generate_freeze_manifest.py",
    "source_only_audit/source_sampling_audit_manifest.json",
    "model_artifacts/model_bundle_manifest.json",
    "registration/README.md",
    "registration/0725_OSF_registration_draft_v1.md",
    "registration/0725_timestamp_evidence_plan_v1.yaml",
    "registration/0725_GitHub_release_checklist_v1.md",
    "registration/0725_Zenodo_deposition_checklist_v1.md",
    "registration/0725_registration_upload_inventory_v1.csv",
    "registration/0725_outcome_lock_attestation_template_v1.md",
    "registration/0725_v1.0_freeze_gap_report_v1.md",
]

CSV_REQUIRED_COLUMNS = {
    "03_unit_registry.csv": {
        "record_status", "archive_id", "archive_sha256", "provider", "basin_id",
        "field_id", "well_id", "wellbore_id", "dependence_family_id",
        "qualification_status", "exclusion_reason_code",
    },
    "05_measurement_semantic_contract.csv": {
        "record_status", "variable_role", "canonical_name", "raw_mnemonic",
        "physical_definition", "measurement_location", "original_uom",
        "canonical_uom", "sampling_basis", "conversion", "missing_rule",
        "physical_range_rule", "evidence_source", "ambiguity_status",
        "rop_definition", "operational_state",
    },
    "11_confirmatory_cohort_manifest.csv": {
        "record_status", "archive_id", "archive_sha256", "basin_id", "field_id",
        "dependence_family_id", "T1a_status", "T1b_status", "semantic_status",
        "T2_qualified", "scorable_status_T3", "primary_field_eligible",
    },
    "15_protocol_deviation_log.csv": {
        "deviation_id", "detected_datetime_utc", "unlock_status",
        "deviation_class", "outcome_independent",
        "scientific_decision_rule_changed", "corrective_action",
        "full_cohort_rerun_required", "original_results_retained",
    },
    "parameter_register.csv": {
        "parameter", "value", "category", "evidence_basis", "data_used",
        "decision_date", "outcome_access", "frozen_version", "owner", "status",
    },
    "v1.0_freeze_checklist.csv": {
        "check_id", "requirement", "status", "evidence_path", "checked_by",
        "checked_at_utc", "blocking_if_fail",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--freeze-ready",
        action="store_true",
        help="Fail on placeholders, non-PASS checklist values, example rows, or unhashed manifest entries.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")

    if errors:
        print_report(root, errors, warnings, 0, args.freeze_ready)
        return 1

    for relative in REQUIRED_FILES:
        path = root / relative
        if path.suffix in {".yaml", ".yml"}:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    parsed = yaml.safe_load(handle)
                if not isinstance(parsed, dict):
                    errors.append(f"YAML root must be a mapping: {relative}")
            except Exception as exc:
                errors.append(f"YAML parse error in {relative}: {exc}")
        elif path.suffix == ".json":
            try:
                with path.open("r", encoding="utf-8") as handle:
                    parsed = json.load(handle)
                if not isinstance(parsed, dict):
                    errors.append(f"JSON root must be an object: {relative}")
            except Exception as exc:
                errors.append(f"JSON parse error in {relative}: {exc}")

    for relative, required in CSV_REQUIRED_COLUMNS.items():
        headers, rows = read_csv(root / relative)
        missing = sorted(required - set(headers))
        if missing:
            errors.append(f"{relative} missing columns: {', '.join(missing)}")
        if len(headers) != len(set(headers)):
            errors.append(f"{relative} has duplicate column names")
        if args.freeze_ready:
            for row_number, row in enumerate(rows, start=2):
                if row.get("record_status") in {"EXAMPLE", "TEMPLATE"}:
                    errors.append(
                        f"{relative}:{row_number} contains draft row status "
                        f"{row.get('record_status')}"
                    )

    semantic_headers, semantic_rows = read_csv(
        root / "05_measurement_semantic_contract.csv"
    )
    del semantic_headers
    roles = {row.get("variable_role") for row in semantic_rows}
    if not {"feature", "target"}.issubset(roles):
        errors.append(
            "Measurement-semantic contract must contain both feature and target rows"
        )
    canonical_names = {row.get("canonical_name") for row in semantic_rows}
    required_variables = {
        "measured_depth",
        "weight_on_bit",
        "surface_rotary_speed",
        "standpipe_pressure",
        "rate_of_penetration",
    }
    if not required_variables.issubset(canonical_names):
        errors.append(
            "Measurement-semantic contract lacks required canonical variables: "
            + ", ".join(sorted(required_variables - canonical_names))
        )

    parameter_headers, parameter_rows = read_csv(root / "parameter_register.csv")
    del parameter_headers
    categories = {row.get("category") for row in parameter_rows}
    if not categories.issubset({"A", "B", "C"}):
        errors.append("parameter_register.csv contains a category outside A/B/C")
    duplicate_parameters = duplicates(
        [row.get("parameter", "") for row in parameter_rows]
    )
    if duplicate_parameters:
        errors.append(
            "Duplicate parameters: " + ", ".join(sorted(duplicate_parameters))
        )

    checklist_headers, checklist_rows = read_csv(
        root / "v1.0_freeze_checklist.csv"
    )
    del checklist_headers
    checklist_statuses = {row.get("status") for row in checklist_rows}
    if not checklist_statuses.issubset({"PENDING", "PASS", "FAIL"}):
        errors.append("Freeze checklist contains an invalid status")
    if args.freeze_ready and any(
        row.get("status") != "PASS" for row in checklist_rows
    ):
        errors.append("Freeze-ready mode requires every checklist item to be PASS")

    manifest_path = root / "16_freeze_manifest.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    manifest_files = manifest.get("files", [])
    manifest_paths = [entry.get("path") for entry in manifest_files]
    duplicate_manifest_paths = duplicates(manifest_paths)
    if duplicate_manifest_paths:
        errors.append(
            "Duplicate manifest paths: "
            + ", ".join(sorted(duplicate_manifest_paths))
        )
    for relative in REQUIRED_FILES:
        if relative == "16_freeze_manifest.json":
            continue
        if relative not in manifest_paths:
            errors.append(f"Required file not covered by manifest: {relative}")
    for entry in manifest_files:
        relative = entry.get("path", "")
        digest = entry.get("sha256", "")
        target = root / relative
        if not target.is_file():
            errors.append(f"Manifest references missing file: {relative}")
        if args.freeze_ready:
            if not SHA256_RE.fullmatch(str(digest)):
                errors.append(f"Invalid frozen SHA-256 for {relative}")
            elif sha256(target) != digest:
                errors.append(f"SHA-256 mismatch for {relative}")

    all_text = ""
    placeholder_count = 0
    for relative in REQUIRED_FILES:
        path = root / relative
        text = path.read_text(encoding="utf-8-sig")
        all_text += text
        placeholder_count += text.count(PLACEHOLDER)

    if args.freeze_ready and placeholder_count:
        errors.append(
            f"Freeze-ready mode found {placeholder_count} TO_BE_FROZEN tokens"
        )
    elif placeholder_count:
        warnings.append(
            f"Draft contains {placeholder_count} TO_BE_FROZEN tokens as expected"
        )

    if "No scientific rule may be relaxed" not in all_text:
        errors.append("Non-negotiable no-outcome-driven-rule-change statement missing")

    print_report(root, errors, warnings, placeholder_count, args.freeze_ready)
    return 1 if errors else 0


def duplicates(values: list[str | None]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        normalized = value or ""
        if normalized in seen:
            repeated.add(normalized)
        seen.add(normalized)
    return repeated


def print_report(
    root: Path,
    errors: list[str],
    warnings: list[str],
    placeholder_count: int,
    freeze_ready: bool,
) -> None:
    print(f"Protocol root: {root}")
    print(f"Mode: {'freeze-ready' if freeze_ready else 'draft-structural'}")
    print(f"TO_BE_FROZEN tokens: {placeholder_count}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
    else:
        print("RESULT: PASS (structural validation)")
        if not freeze_ready:
            print("FREEZE READINESS: NOT ASSESSED; run with --freeze-ready")


if __name__ == "__main__":
    sys.exit(main())

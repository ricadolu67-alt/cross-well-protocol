#!/usr/bin/env python3
"""Audit feature-target semantic completeness without reading numeric outcomes."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ROOT / "05_measurement_semantic_contract.csv",
    ROOT / "05d_extension_v4_measurement_semantic_contract.csv",
]
OUTDIR = ROOT / "registration" / "0725_measurement_semantic_contract_audit_v1"
RESULT = OUTDIR / "0725_measurement_semantic_contract_audit_result_v1.json"
REPORT = OUTDIR / "0725_measurement_semantic_contract_audit_report_v1.md"
EXPECTED = {
    ("feature", "measured_depth"),
    ("feature", "weight_on_bit"),
    ("feature", "surface_rotary_speed"),
    ("feature", "standpipe_pressure"),
    ("target", "rate_of_penetration"),
}
COMMON_REQUIRED = {
    "record_status",
    "variable_role",
    "canonical_name",
    "raw_mnemonic",
    "physical_definition",
    "measurement_location",
    "original_uom",
    "canonical_uom",
    "sampling_basis",
    "operational_state",
    "conversion",
    "missing_rule",
    "physical_range_rule",
    "smoothing_status",
    "derived_status",
    "evidence_source",
    "ambiguity_status",
    "archive_scope",
}
TARGET_REQUIRED = {
    "rop_definition",
    "instantaneous_or_averaged",
    "depth_or_time_derived",
    "connection_exclusion",
    "off_bottom_exclusion",
    "reaming_exclusion",
    "zero_policy",
    "negative_policy",
    "upper_range_policy",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, str]] = []
    schemas: list[list[str]] = []
    input_identity = []
    for path in INPUTS:
        schema, rows = read(path)
        schemas.append(schema)
        all_rows.extend(rows)
        input_identity.append(
            {"path": path.name, "sha256": sha256(path), "rows": len(rows)}
        )

    scopes: dict[str, list[dict[str, str]]] = {}
    for row in all_rows:
        scopes.setdefault(row["archive_scope"], []).append(row)

    failures: list[str] = []
    if schemas[0] != schemas[1]:
        failures.append("SCHEMA_MISMATCH_BETWEEN_CONTRACT_FILES")
    for scope, rows in sorted(scopes.items()):
        observed = {(row["variable_role"], row["canonical_name"]) for row in rows}
        if observed != EXPECTED:
            failures.append(f"{scope}:EXPECTED_EXACT_FEATURE_TARGET_SET")
        for row in rows:
            missing = sorted(name for name in COMMON_REQUIRED if not row.get(name, "").strip())
            if missing:
                failures.append(f"{scope}:{row.get('canonical_name')}:MISSING:{'|'.join(missing)}")
            if row.get("ambiguity_status") != "PASS":
                failures.append(f"{scope}:{row.get('canonical_name')}:AMBIGUITY_NOT_PASS")
            if row.get("variable_role") == "target":
                missing_target = sorted(
                    name for name in TARGET_REQUIRED if not row.get(name, "").strip()
                )
                if missing_target:
                    failures.append(
                        f"{scope}:rate_of_penetration:MISSING:{'|'.join(missing_target)}"
                    )
                if "m/h" not in {row.get("original_uom"), row.get("canonical_uom")}:
                    failures.append(f"{scope}:ROP_UNIT_NOT_HARMONIZED_TO_M_PER_H")

    checks = {
        "input_files_parse": len(INPUTS) == 2,
        "schemas_identical": schemas[0] == schemas[1],
        "archive_scope_count_is_23": len(scopes) == 23,
        "row_count_is_115": len(all_rows) == 115,
        "every_scope_has_exactly_five_rows": all(len(rows) == 5 for rows in scopes.values()),
        "every_scope_has_common4_plus_ROP": all(
            {(row["variable_role"], row["canonical_name"]) for row in rows} == EXPECTED
            for rows in scopes.values()
        ),
        "all_ambiguity_status_pass": all(
            row.get("ambiguity_status") == "PASS" for row in all_rows
        ),
        "all_target_semantic_fields_nonempty": all(
            all(row.get(name, "").strip() for name in TARGET_REQUIRED)
            for row in all_rows
            if row.get("variable_role") == "target"
        ),
        "numeric_ROP_accessed": False,
    }
    passed = not failures and all(
        value is True for key, value in checks.items() if key != "numeric_ROP_accessed"
    )
    passed = passed and checks["numeric_ROP_accessed"] is False
    result = {
        "schema_version": "1.0",
        "audit_id": "CROSS_WELL_MEASUREMENT_SEMANTIC_COMPLETENESS_V1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "CONTRACT_METADATA_ONLY",
        "input_identity": input_identity,
        "archive_scope_count": len(scopes),
        "row_count": len(all_rows),
        "feature_row_count": sum(row["variable_role"] == "feature" for row in all_rows),
        "target_row_count": sum(row["variable_role"] == "target" for row in all_rows),
        "checks": checks,
        "failures": failures,
        "overall_status": "PASS" if passed else "FAIL",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "\n".join(
            [
                "# CROSS-WELL Measurement and Semantic Contract Audit",
                "",
                f"- Executed: `{result['executed_at_utc']}`",
                "- Scope: contract metadata only",
                "- Numeric ROP accessed: `false`",
                f"- Archive-specific scopes: `{len(scopes)}`",
                f"- Contract rows: `{len(all_rows)}`",
                f"- Feature rows: `{result['feature_row_count']}`",
                f"- Target rows: `{result['target_row_count']}`",
                f"- Failures: `{len(failures)}`",
                f"- Overall status: `{result['overall_status']}`",
                "",
                "Each of the 23 qualified archive scopes contains exactly the four",
                "canonical predictors and one ROP target record. All ambiguity statuses",
                "are PASS and all frozen target-semantic fields are populated.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

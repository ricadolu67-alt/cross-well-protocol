#!/usr/bin/env python3
"""Build archive-specific feature-target semantic rows from T1b header/QC evidence."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
T1B = ROOT.parent / "0725_CROSS_WELL_T1b_label_blinded_v4"
FAMILY = T1B / "0725_T1b_family_covariate_QC_v1.csv"
FILES = T1B / "0725_T1b_LAS_file_covariate_QC_v1.csv"
EXT_T1B = ROOT.parent / "0725_CROSS_WELL_extension_T1b_v1"
EXT_FAMILY = EXT_T1B / "0725_extension_T1b_family_QC_v1.csv"
EXT_FILES = EXT_T1B / "0725_extension_T1b_LAS_file_QC_v1.csv"
OUTPUT = ROOT / "05_measurement_semantic_contract.csv"

FIELDS = [
    "record_status", "variable_role", "canonical_name", "raw_mnemonic",
    "physical_definition", "measurement_location", "original_uom",
    "canonical_uom", "sampling_basis", "aggregation_window",
    "operational_state", "conversion", "missing_rule",
    "physical_range_rule", "smoothing_status", "derived_status",
    "evidence_source", "ambiguity_status", "rop_definition",
    "instantaneous_or_averaged", "depth_or_time_derived", "window_length",
    "connection_exclusion", "off_bottom_exclusion", "reaming_exclusion",
    "zero_policy", "negative_policy", "upper_range_policy",
    "archive_scope", "notes",
]

FEATURES = {
    "md": {
        "canonical_name": "measured_depth",
        "physical_definition": "Measured depth along the wellbore trajectory",
        "measurement_location": "wellbore trajectory index",
        "canonical_uom": "m",
        "physical_range_rule": "0 <= MD_m <= 15000; violations become unavailable",
    },
    "wob": {
        "canonical_name": "weight_on_bit",
        "physical_definition": "Source-reported surface weight on bit",
        "measurement_location": "surface",
        "canonical_uom": "kkgf",
        "physical_range_rule": "0 <= WOB_kkgf <= 100; violations become unavailable",
    },
    "rpm": {
        "canonical_name": "surface_rotary_speed",
        "physical_definition": "Source-reported surface rotary speed",
        "measurement_location": "surface",
        "canonical_uom": "rpm",
        "physical_range_rule": "0 <= surface_RPM_rpm <= 500; violations become unavailable",
    },
    "spp": {
        "canonical_name": "standpipe_pressure",
        "physical_definition": "Source-reported standpipe pressure",
        "measurement_location": "surface",
        "canonical_uom": "kPa",
        "physical_range_rule": "0 <= SPP_kPa <= 70000; violations become unavailable",
    },
}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def conversion(canonical: str, unit: str) -> str:
    normalized = "".join(unit.lower().split())
    table = {
        ("md", "m"): "x1",
        ("md", "ft"): "x0.3048",
        ("wob", "1000lbf"): "x0.45359237_to_kkgf",
        ("wob", "1000kgf"): "x1_to_kkgf",
        ("wob", "klb"): "x0.45359237_to_kkgf",
        ("wob", "klbf"): "x0.45359237_to_kkgf",
        ("wob", "klbm"): "x0.45359237_to_kkgf",
        ("wob", "lbf"): "x0.00045359237_to_kkgf",
        ("rpm", "rpm"): "x1",
        ("rpm", "1/min"): "x1",
        ("rpm", "c/min"): "x1",
        ("spp", "kpa"): "x1",
        ("spp", "psi"): "x6.894757293168_to_kPa",
        ("spp", "psig"): "x6.894757293168_to_kPa",
        ("spp", "mpa"): "x1000_to_kPa",
        ("spp", "bar"): "x100_to_kPa",
    }
    try:
        return table[(canonical, normalized)]
    except KeyError as exc:
        raise ValueError(f"Unsupported frozen conversion: {canonical} {unit}") from exc


def main() -> None:
    families = []
    files = {}
    for source_label, family_path, file_path in (
        ("T1B_V4", FAMILY, FILES),
        ("PREUNLOCK_EXTENSION", EXT_FAMILY, EXT_FILES),
    ):
        for row in read(family_path):
            if row["T1b_descriptive_status"] == "LABEL_BLINDED_QUALIFIED":
                row["_source_label"] = source_label
                families.append(row)
        for row in read(file_path):
            row["_source_label"] = source_label
            files[(row["petroleum_field"], row["nopta_well_id"], row["member_path"])] = row
    output: list[dict[str, str]] = []
    for family in families:
        key = (
            family["petroleum_field"],
            family["nopta_well_id"],
            family["selected_source_object"],
        )
        evidence = files[key]
        scope = (
            f"{family['basin_context']}|{family['petroleum_field']}|"
            f"{family['nopta_well_id']}|{family['selected_source_object']}"
        )
        evidence_source = (
            "../0725_CROSS_WELL_T1b_label_blinded_v4/"
            "0725_T1b_LAS_file_covariate_QC_v1.csv"
            if family["_source_label"] == "T1B_V4"
            else "../0725_CROSS_WELL_extension_T1b_v1/"
            "0725_extension_T1b_LAS_file_QC_v1.csv"
        )
        for prefix, specification in FEATURES.items():
            raw = evidence[f"{prefix}_raw_mnemonic"]
            unit = evidence[f"{prefix}_declared_unit"]
            row = {field: "" for field in FIELDS}
            row.update(
                {
                    "record_status": "DRAFT_ARCHIVE_SPECIFIC_PASS",
                    "variable_role": "feature",
                    "canonical_name": specification["canonical_name"],
                    "raw_mnemonic": raw,
                    "physical_definition": specification["physical_definition"],
                    "measurement_location": specification["measurement_location"],
                    "original_uom": unit,
                    "canonical_uom": specification["canonical_uom"],
                    "sampling_basis": "native depth-indexed source object",
                    "aggregation_window": "source reported or unknown",
                    "operational_state": "drilling-surface lineage in selected header",
                    "conversion": conversion(prefix, unit),
                    "missing_rule": "mark unavailable; frozen source median after family qualification",
                    "physical_range_rule": specification["physical_range_rule"],
                    "smoothing_status": "source reported; no new smoothing",
                    "derived_status": "source-reported engineering curve",
                    "evidence_source": evidence_source,
                    "ambiguity_status": "PASS",
                    "archive_scope": scope,
                    "notes": evidence[f"{prefix}_header_description"],
                }
            )
            output.append(row)

        rop_description = evidence["rop_header_description"]
        lower_description = rop_description.lower()
        is_five_foot = "5ft" in lower_description or "last 5 ft" in lower_description
        is_average = "averag" in lower_description or is_five_foot
        rop_unit = evidence["rop_declared_unit"]
        normalized_rop_unit = rop_unit.lower().replace(" ", "")
        if normalized_rop_unit not in {"m/h", "m/hr"}:
            raise ValueError(f"Unsupported ROP unit without numeric access: {rop_unit}")
        target = {field: "" for field in FIELDS}
        target.update(
            {
                "record_status": "PRINCIPALLY_FROZEN_ARCHIVE_SPECIFIC_PASS",
                "variable_role": "target",
                "canonical_name": "rate_of_penetration",
                "raw_mnemonic": evidence["rop_raw_mnemonic"],
                "physical_definition": (
                    "Source-reported operational rate of penetration representing "
                    "new-hole advancement during eligible active-drilling intervals"
                ),
                "measurement_location": "wellbore advancement",
                "original_uom": rop_unit,
                "canonical_uom": "m/h",
                "sampling_basis": "native depth-indexed source object",
                "aggregation_window": (
                    "5 ft (approximately 1.5 m) source window"
                    if is_five_foot else "source reported average window or unknown"
                ),
                "operational_state": "drilling-surface lineage in selected header",
                "conversion": "x1_to_m_per_h",
                "missing_rule": "exclude nonfinite target and count",
                "physical_range_rule": "finite and strictly positive; no upper truncation",
                "smoothing_status": "source reported; no new smoothing",
                "derived_status": "source-reported measured or derived lineage recorded",
                "evidence_source": evidence_source,
                "ambiguity_status": "PASS",
                "rop_definition": rop_description,
                "instantaneous_or_averaged": (
                    "averaged" if is_average else "source reported or unknown"
                ),
                "depth_or_time_derived": "source-reported depth-indexed curve",
                "window_length": (
                    "5 ft (approximately 1.5 m)" if is_five_foot else "unknown"
                ),
                "connection_exclusion": "exclude when explicitly flagged",
                "off_bottom_exclusion": "exclude when explicitly flagged or require drilling-only lineage",
                "reaming_exclusion": "exclude when explicitly flagged or require new-hole lineage",
                "zero_policy": "exclude and count",
                "negative_policy": "exclude and count",
                "upper_range_policy": "retain finite positive extremes and flag",
                "archive_scope": scope,
                "notes": "ROP numeric payload remained inaccessible when this row was generated",
            }
        )
        output.append(target)

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(f"Wrote {len(output)} semantic rows for {len(families)} qualified families")


if __name__ == "__main__":
    main()

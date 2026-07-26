#!/usr/bin/env python3
"""Build a principal-review packet from label-blinded integration metadata."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT.parent / "0725_CROSS_WELL_preunlock_integration_v4"
FAMILIES = INPUT_DIR / "0725_combined_T1b_family_status_v4.csv"
FIELDS = INPUT_DIR / "0725_combined_T1b_field_status_v4.csv"
OUT = ROOT / "registration" / "0725_principal_dependence_cohort_review_v1"
REVIEW = OUT / "0725_principal_dependence_cohort_review_v1.csv"
FIELD_REVIEW = OUT / "0725_principal_field_review_v1.csv"
REPORT = OUT / "0725_principal_dependence_cohort_review_report_v1.md"
MANIFEST = OUT / "0725_principal_dependence_cohort_review_manifest_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def slug(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    families = rows(FAMILIES)
    fields = rows(FIELDS)
    review_rows = []
    ids = []
    for row in families:
        nopta = row["nopta_well_id"].strip()
        family_id = f"LD_NOPTA_{nopta}" if nopta else f"LD_{slug(row['petroleum_field'])}_{slug(row['well_name'])}"
        ids.append(family_id)
        qualified = row["T1b_descriptive_status"] == "LABEL_BLINDED_QUALIFIED"
        review_rows.append(
            {
                "dependence_family_id": family_id,
                "basin_context": row["basin_context"],
                "petroleum_field": row["petroleum_field"],
                "nopta_well_id": nopta,
                "well_name": row["well_name"],
                "archive_names": row["archive_names"],
                "selected_source_object": row["selected_source_object"],
                "T1b_descriptive_status": row["T1b_descriptive_status"],
                "qualification_decision": "QUALIFIED" if qualified else "HELD",
                "dependence_rule": "ONE_TRACEABLE_NOPTA_WELL_ID_PER_CONSERVATIVE_FAMILY",
                "cross_row_merge_proposed": "false",
                "component_branch_retained_within_family": "true" if re.search(r"\bST\d*\b|SIDETRACK", row["well_name"], re.I) else "not_applicable",
                "numeric_ROP_accessed": "false",
                "proposed_principal_decision": "ACCEPT",
                "principal_review_status": "TO_BE_REVIEWED",
                "principal_review_notes": "",
            }
        )
    fields_out = []
    for row in fields:
        fields_out.append(
            {
                "basin_context": row["basin_context"],
                "petroleum_field": row["petroleum_field"],
                "development_family_count": row["development_family_count"],
                "label_blinded_qualified_family_count": row["label_blinded_qualified_family_count"],
                "held_family_count": row["held_family_count"],
                "primary_qualification_status": row["primary_qualification_status"],
                "proposed_primary_field_decision": (
                    "INCLUDE_PRIMARY_IF_AT_LEAST_TWO_SCORABLE_AFTER_UNLOCK"
                    if row["qualified_family_count_ge_2"].lower() == "true"
                    else "RETAIN_IN_FLOW_NOT_PRIMARY_PREUNLOCK"
                ),
                "numeric_ROP_accessed": "false",
                "principal_review_status": "TO_BE_REVIEWED",
                "principal_review_notes": "",
            }
        )
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    with FIELD_REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields_out[0]))
        writer.writeheader()
        writer.writerows(fields_out)
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    qualified_count = sum(r["qualification_decision"] == "QUALIFIED" for r in review_rows)
    primary_fields = sum(
        r["proposed_primary_field_decision"].startswith("INCLUDE_PRIMARY") for r in fields_out
    )
    basin_count = len(
        {
            r["basin_context"]
            for r in fields_out
            if r["proposed_primary_field_decision"].startswith("INCLUDE_PRIMARY")
        }
    )
    passed = (
        len(review_rows) == 36
        and qualified_count == 23
        and len(fields_out) == 13
        and primary_fields == 8
        and basin_count == 5
        and not duplicates
    )
    REPORT.write_text(
        "\n".join(
            [
                "# Principal Dependence and Cohort Review Packet",
                "",
                f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
                "- Source: integration-v4 label-blinded metadata only",
                "- Numeric ROP accessed: `false`",
                f"- Development families: `{len(review_rows)}`",
                f"- Qualified families: `{qualified_count}`",
                f"- Petroleum fields: `{len(fields_out)}`",
                f"- Proposed primary fields: `{primary_fields}`",
                f"- Represented primary basin contexts: `{basin_count}`",
                f"- Duplicate proposed family IDs: `{len(duplicates)}`",
                f"- Packet validation: `{'PASS' if passed else 'FAIL'}`",
                "",
                "## Proposed rule",
                "",
                "Each traceable NOPTA well ID is one conservative dependence family.",
                "A sidetrack or branch named inside that well record remains inside the",
                "same family. No separate qualified rows share a NOPTA ID, and no",
                "cross-row merge is proposed. Held families remain visible in the flow.",
                "",
                "## Required principal action",
                "",
                "Review the two CSV files and either accept the complete proposed",
                "registry or identify exact rows requiring correction. Acceptance will",
                "close F06 and permit generation of the final preunlock cohort manifest",
                "for F15. It does not authorize numeric outcome access.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0",
        "packet_status": "READY_FOR_PRINCIPAL_REVIEW" if passed else "FAILED_VALIDATION",
        "numeric_ROP_accessed": False,
        "inputs": [
            {"path": str(FAMILIES), "sha256": sha256(FAMILIES)},
            {"path": str(FIELDS), "sha256": sha256(FIELDS)},
        ],
        "outputs": [
            {"path": REVIEW.name, "sha256": sha256(REVIEW), "rows": len(review_rows)},
            {"path": FIELD_REVIEW.name, "sha256": sha256(FIELD_REVIEW), "rows": len(fields_out)},
            {"path": REPORT.name, "sha256": sha256(REPORT)},
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

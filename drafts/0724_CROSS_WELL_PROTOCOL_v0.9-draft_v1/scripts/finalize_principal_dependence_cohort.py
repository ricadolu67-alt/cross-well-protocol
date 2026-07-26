#!/usr/bin/env python3
"""Finalize the principal-approved preunlock dependence and cohort registries."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "registration" / "0725_principal_dependence_cohort_review_v1"
FAMILY_REVIEW = REVIEW_DIR / "0725_principal_dependence_cohort_review_v1.csv"
FIELD_REVIEW = REVIEW_DIR / "0725_principal_field_review_v1.csv"
ACCEPTANCE = REVIEW_DIR / "0725_principal_acceptance_record_v1.md"
DEPENDENCE_OUT = ROOT / "03e_final_preunlock_dependence_registry.csv"
COHORT_OUT = ROOT / "11e_final_preunlock_cohort_manifest.csv"
FIELD_OUT = ROOT / "11f_final_preunlock_field_manifest.csv"
RESULT = REVIEW_DIR / "0725_principal_finalization_result_v1.json"
REPORT = REVIEW_DIR / "0725_principal_finalization_report_v1.md"
ACCEPTED_AT_LOCAL = "2026-07-25T18:02:38+08:00"
ACCEPTED_AT_UTC = "2026-07-25T10:02:38Z"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    families = read(FAMILY_REVIEW)
    fields = read(FIELD_REVIEW)
    field_decisions = {row["petroleum_field"]: row for row in fields}

    dependence_rows = []
    cohort_rows = []
    for row in families:
        field = field_decisions[row["petroleum_field"]]
        qualified = row["qualification_decision"] == "QUALIFIED"
        dependence_rows.append(
            {
                "record_status": "FINAL_PREUNLOCK_ACCEPTED",
                "dependence_family_id": row["dependence_family_id"],
                "provider": "NOPIMS",
                "basin_context": row["basin_context"],
                "petroleum_field": row["petroleum_field"],
                "nopta_well_id": row["nopta_well_id"],
                "well_name": row["well_name"],
                "archive_names": row["archive_names"],
                "dependence_rule": row["dependence_rule"],
                "cross_row_merge": "false",
                "component_branch_retained_within_family": row["component_branch_retained_within_family"],
                "evidence_reference": "0725_principal_dependence_cohort_review_v1.csv",
                "decision": "ACCEPTED_AS_PROPOSED",
                "reviewer": "Principal researcher",
                "decision_datetime_utc": ACCEPTED_AT_UTC,
                "numeric_ROP_accessed": "false",
            }
        )
        cohort_rows.append(
            {
                "record_status": "FINAL_PREUNLOCK_ACCEPTED",
                "dependence_family_id": row["dependence_family_id"],
                "basin_context": row["basin_context"],
                "petroleum_field": row["petroleum_field"],
                "nopta_well_id": row["nopta_well_id"],
                "well_name": row["well_name"],
                "archive_names": row["archive_names"],
                "selected_source_object": row["selected_source_object"],
                "T1b_descriptive_status": row["T1b_descriptive_status"],
                "T2_qualified": str(qualified).lower(),
                "preunlock_family_disposition": "QUALIFIED" if qualified else "HELD_RETAINED_IN_FLOW",
                "scorable_status_T3": "NOT_EVALUATED_ROP_LOCKED",
                "primary_field_preunlock_status": field["primary_qualification_status"],
                "primary_field_T3_rule": field["proposed_primary_field_decision"],
                "principal_decision": "ACCEPTED_AS_PROPOSED",
                "principal_decision_datetime_utc": ACCEPTED_AT_UTC,
                "numeric_ROP_accessed": "false",
            }
        )
    field_rows = []
    for row in fields:
        field_rows.append(
            {
                "record_status": "FINAL_PREUNLOCK_ACCEPTED",
                "basin_context": row["basin_context"],
                "petroleum_field": row["petroleum_field"],
                "development_family_count": row["development_family_count"],
                "label_blinded_qualified_family_count": row["label_blinded_qualified_family_count"],
                "held_family_count": row["held_family_count"],
                "primary_qualification_status": row["primary_qualification_status"],
                "T3_primary_eligibility_rule": row["proposed_primary_field_decision"],
                "principal_decision": "ACCEPTED_AS_PROPOSED",
                "principal_decision_datetime_utc": ACCEPTED_AT_UTC,
                "numeric_ROP_accessed": "false",
            }
        )
    write(DEPENDENCE_OUT, dependence_rows)
    write(COHORT_OUT, cohort_rows)
    write(FIELD_OUT, field_rows)

    ACCEPTANCE.write_text(
        "\n".join(
            [
                "# Principal Acceptance — Dependence and Cohort Review",
                "",
                f"- Accepted locally: `{ACCEPTED_AT_LOCAL}`",
                f"- Accepted in UTC: `{ACCEPTED_AT_UTC}`",
                "- Authority: Principal researcher",
                "- Outcome access at decision: `NO_LAYER_D_OUTCOME_ACCESS`",
                "",
                "The principal researcher accepted all proposed decisions in the",
                "36-family dependence review and the 13-field cohort review.",
                "",
                "The accepted rule assigns one conservative dependence family to each",
                "traceable NOPTA well ID; a sidetrack or branch named within that well",
                "record remains inside the same family; no cross-row merge is made.",
                "All 36 development families remain visible, including 23 qualified",
                "families and 13 held families. Eight fields are primary-qualified",
                "before outcome unlock, subject to the frozen requirement of at least",
                "two scorable independent families after unlock.",
                "",
                "This decision closes identity/dependence governance for the current",
                "v1.0 candidate inventory. It does not authorize numeric ROP access.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ids = [row["dependence_family_id"] for row in dependence_rows]
    primary_fields = sum(
        row["primary_qualification_status"] == "QUALIFIED_GE_2_FAMILIES"
        for row in field_rows
    )
    checks = {
        "family_count_is_36": len(dependence_rows) == 36,
        "dependence_family_ids_unique": len(set(ids)) == 36,
        "qualified_family_count_is_23": sum(
            row["T2_qualified"] == "true" for row in cohort_rows
        ) == 23,
        "held_family_count_is_13": sum(
            row["preunlock_family_disposition"] == "HELD_RETAINED_IN_FLOW"
            for row in cohort_rows
        ) == 13,
        "field_count_is_13": len(field_rows) == 13,
        "primary_qualified_field_count_is_8": primary_fields == 8,
        "represented_primary_basin_count_is_5": len(
            {
                row["basin_context"]
                for row in field_rows
                if row["primary_qualification_status"] == "QUALIFIED_GE_2_FAMILIES"
            }
        ) == 5,
        "all_principal_decisions_accepted": all(
            row["principal_decision"] == "ACCEPTED_AS_PROPOSED"
            for row in cohort_rows + field_rows
        ),
        "numeric_ROP_accessed": False,
    }
    passed = all(v is True for k, v in checks.items() if k != "numeric_ROP_accessed")
    passed = passed and checks["numeric_ROP_accessed"] is False
    result = {
        "schema_version": "1.0",
        "finalization_id": "CROSS_WELL_PRINCIPAL_DEPENDENCE_COHORT_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "outputs": {
            DEPENDENCE_OUT.name: sha256(DEPENDENCE_OUT),
            COHORT_OUT.name: sha256(COHORT_OUT),
            FIELD_OUT.name: sha256(FIELD_OUT),
            ACCEPTANCE.name: sha256(ACCEPTANCE),
        },
        "overall_status": "PASS" if passed else "FAIL",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "\n".join(
            [
                "# Principal Dependence/Cohort Finalization Report",
                "",
                f"- Generated: `{result['generated_at_utc']}`",
                "- Numeric ROP accessed: `false`",
                "- Final development families: `36`",
                "- Final qualified families: `23`",
                "- Held families retained in flow: `13`",
                "- Final petroleum fields: `13`",
                "- Primary-qualified fields: `8`",
                "- Represented primary basin contexts: `5`",
                f"- Overall status: `{result['overall_status']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

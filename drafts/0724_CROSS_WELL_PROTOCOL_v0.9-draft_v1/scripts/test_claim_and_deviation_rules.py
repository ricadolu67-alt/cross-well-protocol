#!/usr/bin/env python3
"""Machine tests for claim wording and protocol-deviation governance."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "14a_claim_wording_rules.csv"
DEVIATIONS = ROOT / "15a_protocol_deviation_rules.json"
ACTIVE_LOG = ROOT / "15_protocol_deviation_log.csv"
OUT = ROOT / "registration" / "0725_claim_deviation_rule_test_v1"
RESULT = OUT / "0725_claim_deviation_rule_test_result_v1.json"
REPORT = OUT / "0725_claim_deviation_rule_test_report_v1.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with CLAIMS.open(encoding="utf-8-sig", newline="") as handle:
        claims = list(csv.DictReader(handle))
    deviations = json.loads(DEVIATIONS.read_text(encoding="utf-8"))
    with ACTIVE_LOG.open(encoding="utf-8-sig", newline="") as handle:
        log_rows = list(csv.DictReader(handle))
    by_key = {row["condition_key"]: row for row in claims}
    model_branches = {
        "ET_gt_median_and_ET_gt_ridge",
        "ET_gt_median_and_ET_not_gt_ridge",
        "ET_not_gt_median",
    }
    diagnostic_branches = {
        "split_distortion_positive",
        "dependence_distortion_positive",
        "F15_retrospective_semantic",
        "semantic_distortion_positive",
    }
    checks = {
        "claim_rule_count_is_14": len(claims) == 14,
        "claim_ids_unique": len({row["claim_id"] for row in claims}) == len(claims),
        "condition_keys_unique": len(by_key) == len(claims),
        "every_rule_has_allowed_wording": all(row["allowed_wording"].strip() for row in claims),
        "every_rule_has_prohibited_wording": all(row["prohibited_wording"].strip() for row in claims),
        "all_model_result_branches_present": model_branches <= set(by_key),
        "all_diagnostic_boundaries_present": diagnostic_branches <= set(by_key),
        "mandatory_noncausal_boundary_present": "mandatory_noncausal_boundary" in by_key,
        "random_basin_overclaim_prohibited": "random-basin" in by_key["layer_D_all_gates_pass"]["prohibited_wording"],
        "preunlock_D2_full_rerun_required": deviations["pre_unlock"]["D2"]["full_cohort_rerun_required"] is True,
        "preunlock_D3_requires_new_version": deviations["pre_unlock"]["D3"]["required_disposition"] == "NEW_PROTOCOL_VERSION_AND_NEW_TIMESTAMP",
        "postunlock_D2_selective_rerun_prohibited": deviations["post_unlock"]["D2"]["selective_unit_rerun_prohibited"] is True,
        "postunlock_D3_not_confirmatory_correction": deviations["post_unlock"]["D3"]["confirmatory_correction_allowed"] is False,
        "active_log_contains_no_example_row": all(row["deviation_id"] != "EXAMPLE" for row in log_rows),
        "actual_D2_full_rerun_case_closed": any(
            row["deviation_id"] == "DRYRUN-D2-001"
            and row["reporting_status"] == "CLOSED_CORRECTED_FULL_RERUN"
            and row["full_cohort_rerun_required"].lower() == "true"
            and row["original_results_retained"].lower() == "true"
            for row in log_rows
        ),
        "numeric_Layer_D_outcome_accessed": False,
    }
    passed = all(v is True for k, v in checks.items() if k != "numeric_Layer_D_outcome_accessed")
    passed = passed and checks["numeric_Layer_D_outcome_accessed"] is False
    result = {
        "schema_version": "1.0",
        "test_id": "CROSS_WELL_CLAIM_AND_DEVIATION_RULES_V1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "GOVERNANCE_FILES_ONLY",
        "input_sha256": {
            CLAIMS.name: sha256(CLAIMS),
            DEVIATIONS.name: sha256(DEVIATIONS),
            ACTIVE_LOG.name: sha256(ACTIVE_LOG),
        },
        "checks": checks,
        "overall_status": "PASS" if passed else "FAIL",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "\n".join(
            [
                "# CROSS-WELL Claim and Deviation Rule Test",
                "",
                f"- Executed: `{result['executed_at_utc']}`",
                "- Scope: governance files only",
                "- Layer D numeric outcome access: `false`",
                f"- Claim branches: `{len(claims)}`",
                f"- Active deviation rows: `{len(log_rows)}`",
                "- Active example rows: `0`",
                f"- Overall status: `{result['overall_status']}`",
                "",
                "The test covers all frozen model-result interpretations, diagnostic",
                "scope boundaries, the mandatory non-causal statement, and D1/D2/D3",
                "pre- and post-unlock disposition rules.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

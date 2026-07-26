#!/usr/bin/env python3
"""Single-use fail-closed Layer D confirmatory execution.

The program refuses to open any selected LAS member until an external unlock
gate proves that the frozen payload was timestamped and that the principal
researcher explicitly authorized the named run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
import sys
import traceback
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uncertainty_plan import (
    field_bootstrap,
    reml_random_intercept,
    stratified_bootstrap,
    wild_cluster_interval,
)


FEATURE_ORDER = ["MD_m", "WOB_1000_kgf", "surface_RPM_rpm", "SPP_kPa"]
PHYSICAL_RANGES = {
    "MD_m": (0.0, 15000.0),
    "WOB_1000_kgf": (0.0, 100.0),
    "surface_RPM_rpm": (0.0, 500.0),
    "SPP_kPa": (0.0, 70000.0),
}
SEEDS = [20260722, 20260723, 20260724, 20260725, 20260726]
PROTOCOL_VERSION = "CROSS_WELL_PROTOCOL_v1.0-frozen"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_from_shell(root: Path, output: Path, name: str, rows: list[dict]) -> Path:
    shell = root / "13_output_table_shells" / name
    with shell.open(encoding="utf-8-sig", newline="") as handle:
        fields = list(csv.DictReader(handle).fieldnames or [])
    target = output / name
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return target


def normalized_mnemonic(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def parse_header_item(line: str) -> tuple[str, str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "." not in stripped:
        return None
    left, _, description = stripped.partition(":")
    mnemonic, _, rest = left.partition(".")
    tokens = rest.strip().split()
    unit = tokens[0] if tokens else ""
    if len(tokens) >= 2 and re.fullmatch(r"1000(?:\.0+)?", tokens[0]):
        unit = f"{tokens[0]} {tokens[1]}"
    return mnemonic.strip(), unit, description.strip()


def conversion_factor(rule: str) -> float:
    factors = {
        "x1": 1.0,
        "x1_to_m_per_h": 1.0,
        "x0.3048_to_m": 0.3048,
        "x0.45359237_to_kkgf": 0.45359237,
        "x0.001_to_kkgf": 0.001,
        "x6.894757293168_to_kPa": 6.894757293168,
        "x1000_to_kPa": 1000.0,
        "x100_to_kPa": 100.0,
    }
    if rule not in factors:
        raise ValueError(f"Unrecognized frozen conversion: {rule}")
    return factors[rule]


def load_las_rows(source: dict[str, str], archive_path: str | None = None) -> list[dict]:
    archive = Path(archive_path or source.get("archive_path", ""))
    if not archive.is_file():
        raise RuntimeError(f"Resolved archive path is missing: {archive}")
    if sha256(archive) != source["archive_sha256"].upper():
        raise RuntimeError(f"Archive hash mismatch: {archive}")
    with zipfile.ZipFile(archive) as zf:
        payload = zf.read(source["selected_source_object"])
    text = payload.decode("utf-8", errors="replace")
    curves: list[tuple[str, str, str]] = []
    data_lines: list[str] = []
    in_curve = False
    in_data = False
    null_value: float | None = None
    for line in text.splitlines():
        upper = line.lstrip().upper()
        if upper.startswith("~"):
            in_curve = upper.startswith("~C")
            in_data = upper.startswith("~A")
            continue
        if in_data:
            if line.strip() and not line.lstrip().startswith("#"):
                data_lines.append(line)
            continue
        item = parse_header_item(line)
        if item and normalized_mnemonic(item[0]) == "NULL":
            try:
                null_value = float(line.partition(".")[2].split(":")[0].strip().split()[-1])
            except Exception:
                null_value = None
        if in_curve and item:
            curves.append(item)
    if not curves or not data_lines:
        raise RuntimeError("Selected LAS object lacks a parseable curve or data section")
    indices: dict[str, int] = {}
    for key, field in [
        ("MD_m", "md_mnemonic"),
        ("WOB_1000_kgf", "wob_mnemonic"),
        ("surface_RPM_rpm", "rpm_mnemonic"),
        ("SPP_kPa", "spp_mnemonic"),
        ("ROP_m_per_h", "rop_mnemonic"),
    ]:
        wanted = normalized_mnemonic(source[field])
        found = [i for i, item in enumerate(curves) if normalized_mnemonic(item[0]) == wanted]
        if len(found) != 1:
            raise RuntimeError(f"Frozen mnemonic {source[field]!r} resolved {len(found)} times")
        indices[key] = found[0]
    factors = {
        "MD_m": conversion_factor(source["md_conversion"]),
        "WOB_1000_kgf": conversion_factor(source["wob_conversion"]),
        "surface_RPM_rpm": conversion_factor(source["rpm_conversion"]),
        "SPP_kPa": conversion_factor(source["spp_conversion"]),
        "ROP_m_per_h": conversion_factor(source["rop_conversion"]),
    }
    rows: list[dict] = []
    segment = 0
    previous_md: float | None = None
    previous_eligible = False
    for line_number, line in enumerate(data_lines, start=1):
        tokens = re.split(r"[\s,]+", line.strip())
        if len(tokens) < len(curves):
            previous_eligible = False
            continue
        values: dict[str, float] = {}
        valid = True
        for key, index in indices.items():
            try:
                raw = float(tokens[index])
            except (ValueError, OverflowError):
                raw = math.nan
            if null_value is not None and math.isfinite(raw) and math.isclose(raw, null_value, rel_tol=0.0, abs_tol=1e-12):
                raw = math.nan
            values[key] = raw * factors[key] if math.isfinite(raw) else math.nan
        md = values["MD_m"]
        rop = values["ROP_m_per_h"]
        if not math.isfinite(md) or not math.isfinite(rop) or rop <= 0:
            previous_eligible = False
            continue
        if not (PHYSICAL_RANGES["MD_m"][0] <= md <= PHYSICAL_RANGES["MD_m"][1]):
            previous_eligible = False
            continue
        for feature in FEATURE_ORDER[1:]:
            value = values[feature]
            low, high = PHYSICAL_RANGES[feature]
            if math.isfinite(value) and not (low <= value <= high):
                values[feature] = math.nan
        if (
            not previous_eligible
            or previous_md is None
            or md < previous_md
            or md - previous_md > 1.0
        ):
            segment += 1
        rows.append({
            **values,
            "continuous_segment_id": f"S{segment:05d}",
            "stable_original_row_id": f"L{line_number:09d}",
        })
        previous_md = md
        previous_eligible = valid
    return rows


def score_family(rows: list[dict], predictors: dict[str, np.ndarray]) -> dict[str, dict[str, float | int | bool]]:
    expanded = []
    for index, row in enumerate(rows):
        entry = dict(row)
        for key, values in predictors.items():
            entry[key] = float(values[index])
        expanded.append(entry)
    grouped: dict[tuple[str, float], list[dict]] = defaultdict(list)
    for row in sorted(expanded, key=lambda item: (item["continuous_segment_id"], item["MD_m"], item["stable_original_row_id"])):
        grouped[(row["continuous_segment_id"], row["MD_m"])].append(row)
    points_by_segment: dict[str, list[dict]] = defaultdict(list)
    for (segment, md), group in grouped.items():
        point = {"md": md, "y": statistics.median(item["ROP_m_per_h"] for item in group)}
        for key in predictors:
            point[key] = statistics.median(item[key] for item in group)
        points_by_segment[segment].append(point)
    weighted_errors = {key: 0.0 for key in predictors}
    total_weight = 0.0
    coverage = 0.0
    point_count = 0
    valid_segments = 0
    weighted_points: list[dict] = []
    for points in points_by_segment.values():
        points.sort(key=lambda item: item["md"])
        if len(points) < 2:
            continue
        valid_segments += 1
        coverage += points[-1]["md"] - points[0]["md"]
        point_count += len(points)
        for idx, point in enumerate(points):
            if idx == 0:
                weight = min((points[1]["md"] - point["md"]) / 2.0, 0.5)
            elif idx == len(points) - 1:
                weight = min((point["md"] - points[idx - 1]["md"]) / 2.0, 0.5)
            else:
                weight = min((points[idx + 1]["md"] - points[idx - 1]["md"]) / 2.0, 0.5)
            if not math.isfinite(weight) or weight <= 0:
                continue
            total_weight += weight
            for key in predictors:
                weighted_errors[key] += weight * abs(point["y"] - point[key])
            weighted_points.append({**point, "weight": weight})
    scorable = coverage >= 100.0 and point_count >= 100 and valid_segments >= 1 and total_weight > 0
    result: dict[str, dict[str, float | int | bool]] = {}
    for key in predictors:
        result[key] = {
            "mae": weighted_errors[key] / total_weight if total_weight else math.nan,
            "coverage": coverage,
            "points": point_count,
            "segments": valid_segments,
            "scorable": scorable,
            "block_mae": fixed_block_mae(weighted_points, key),
        }
    return result


def fixed_block_mae(points: list[dict], key: str) -> float:
    blocks: dict[int, list[dict]] = defaultdict(list)
    for point in points:
        blocks[math.floor(point["md"] / 1.0)].append(point)
    errors = []
    for group in blocks.values():
        weight = sum(item["weight"] for item in group)
        if weight < 0.5:
            continue
        observed = sum(item["weight"] * item["y"] for item in group) / weight
        predicted = sum(item["weight"] * item[key] for item in group) / weight
        errors.append(abs(observed - predicted))
    return statistics.fmean(errors) if errors else math.nan


def validate_gate(root: Path, gate_path: Path, locator_path: Path) -> dict:
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    required_true = [
        "osf_registration_completed", "github_signed_release_completed",
        "outcome_lock_reconfirmed", "principal_single_use_authorization",
        "all_payload_ready_checks_passed",
    ]
    missing = [key for key in required_true if gate.get(key) is not True]
    if missing:
        raise RuntimeError("External unlock gate is not PASS: " + ", ".join(missing))
    if gate.get("authorized_by") != "Lu Yuhan":
        raise RuntimeError("Single-use authorization is not from the frozen authority")
    manifest_hash = sha256(root / "16_freeze_manifest.json")
    if gate.get("freeze_manifest_sha256", "").upper() != manifest_hash:
        raise RuntimeError("External gate does not identify this freeze manifest")
    if not gate.get("osf_registration_url") or not gate.get("github_release_url"):
        raise RuntimeError("External evidence URLs are missing")
    if gate.get("local_archive_locator_sha256", "").upper() != sha256(locator_path):
        raise RuntimeError("Private local archive locator identity mismatch")
    return gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol-root", required=True)
    parser.add_argument("--unlock-gate", required=True)
    parser.add_argument("--archive-locator", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.protocol_root).resolve()
    gate_path = Path(args.unlock_gate).resolve()
    locator_path = Path(args.archive_locator).resolve()
    output = Path(args.output_root).resolve()
    if output.exists():
        raise SystemExit("Output directory must not already exist")
    gate = validate_gate(root, gate_path, locator_path)  # Must finish before opening any LAS member.
    output.mkdir(parents=True)
    raw_dir = output / "raw_family_predictions"
    raw_dir.mkdir()
    now = datetime.now(timezone.utc).isoformat()
    trace: list[dict] = []
    trace.append({
        "event_id": "T3-0001", "event_datetime_utc": now,
        "actor_or_process": "run_layer_d_confirmatory.py",
        "event_type": "EXTERNAL_UNLOCK_GATE_VALIDATED", "input_path": str(gate_path),
        "input_sha256": sha256(gate_path), "command_or_action": "fail-closed gate validation",
        "output_path": str(output), "output_sha256": "", "exit_status": "PASS",
        "protocol_version": PROTOCOL_VERSION, "notes": gate.get("single_use_run_id", ""),
    })

    source_map = read_csv(root / "registration" / "0726_frozen_scoring_source_map_v1.csv")
    local_locator = json.loads(locator_path.read_text(encoding="utf-8"))
    path_by_hash = {
        row["archive_sha256"].upper(): row["archive_path"]
        for row in local_locator["archives"]
    }
    bundle = json.loads((root / "model_artifacts" / "model_bundle_manifest.json").read_text(encoding="utf-8"))
    for artifact in bundle["artifacts"]:
        path = root / "model_artifacts" / artifact["path"]
        if sha256(path) != artifact["sha256"].upper():
            raise RuntimeError(f"Model artifact hash mismatch: {path}")
    models = {
        f"et_{seed}": joblib.load(root / "model_artifacts" / f"FrozenExtraTrees_seed_{seed}.joblib")
        for seed in SEEDS
    }
    ridge = joblib.load(root / "model_artifacts" / "FrozenSourceOnlyRidge_alpha100.joblib")
    medians = json.loads((root / "model_artifacts" / "source_feature_medians.json").read_text(encoding="utf-8"))["values"]
    source_median = json.loads((root / "model_artifacts" / "source_median.json").read_text(encoding="utf-8"))["value_m_per_h"]
    family_rows: list[dict] = []
    for source in source_map:
        archive_path = path_by_hash.get(source["archive_sha256"].upper())
        if not archive_path:
            raise RuntimeError(f'No private path for archive hash {source["archive_sha256"]}')
        rows = load_las_rows(source, archive_path)
        frame = pd.DataFrame([{key: row[key] for key in FEATURE_ORDER} for row in rows], columns=FEATURE_ORDER)
        et_frame = frame.fillna({key: medians[key] for key in FEATURE_ORDER})
        predictors = {name: model.predict(et_frame) for name, model in models.items()}
        predictors["ridge"] = ridge.predict(frame)
        predictors["median"] = np.full(len(frame), source_median)
        scored = score_family(rows, predictors)
        et_mae = statistics.fmean(float(scored[f"et_{seed}"]["mae"]) for seed in SEEDS)
        et_block = statistics.fmean(float(scored[f"et_{seed}"]["block_mae"]) for seed in SEEDS)
        reference = scored[f"et_{SEEDS[0]}"]
        scorable = bool(reference["scorable"])
        median_mae = float(scored["median"]["mae"])
        ridge_mae = float(scored["ridge"]["mae"])
        attrition = "" if scorable else "FROZEN_MINIMUM_SCORING_COVERAGE_NOT_MET"
        family_rows.append({
            "basin_id": source["basin_context"], "field_id": source["petroleum_field"],
            "dependence_family_id": source["dependence_family_id"],
            "qualified_status": "QUALIFIED", "scorable_status": "SCORABLE" if scorable else "NOT_SCORABLE",
            "attrition_reason": attrition, "valid_MD_coverage": reference["coverage"],
            "valid_scoring_points": reference["points"], "valid_segments": reference["segments"],
            "MAE_FrozenExtraTrees": et_mae, "MAE_SourceMedian": median_mae,
            "MAE_FrozenSourceOnlyRidge": ridge_mae,
            "transfer_gain_vs_median": median_mae - et_mae if scorable else "",
            "complexity_gain_vs_ridge": ridge_mae - et_mae if scorable else "",
            "log_MAE_ratio_vs_median": math.log(et_mae / median_mae) if scorable and et_mae > 0 and median_mae > 0 else "",
            "fixed_block_MAE_FrozenExtraTrees": et_block,
            "fixed_block_MAE_SourceMedian": scored["median"]["block_mae"],
            "notes": "Five seed-specific family MAEs averaged equally; no ensemble-prediction substitution.",
        })
        raw_path = raw_dir / f'{source["dependence_family_id"].replace("|", "_")}.csv'
        raw_frame = frame.copy()
        raw_frame.insert(0, "stable_original_row_id", [row["stable_original_row_id"] for row in rows])
        raw_frame.insert(0, "continuous_segment_id", [row["continuous_segment_id"] for row in rows])
        raw_frame["ROP_m_per_h"] = [row["ROP_m_per_h"] for row in rows]
        for key, value in predictors.items():
            raw_frame[f"prediction_{key}"] = value
        raw_frame.to_csv(raw_path, index=False, encoding="utf-8-sig")

    scorable = [row for row in family_rows if row["scorable_status"] == "SCORABLE"]
    grouped_fields: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in family_rows:
        grouped_fields[(row["basin_id"], row["field_id"])].append(row)
    field_rows: list[dict] = []
    for (basin, field), group in sorted(grouped_fields.items()):
        eligible = [row for row in group if row["scorable_status"] == "SCORABLE"]
        primary = len(eligible) >= 2
        field_rows.append({
            "basin_id": basin, "field_id": field,
            "n_qualified_families": len(group), "n_scorable_families": len(eligible),
            "primary_field_eligible": str(primary).lower(),
            "field_mean_transfer_gain": statistics.fmean(float(row["transfer_gain_vs_median"]) for row in eligible) if primary else "",
            "field_mean_complexity_gain": statistics.fmean(float(row["complexity_gain_vs_ridge"]) for row in eligible) if primary else "",
            "field_mean_log_MAE_ratio": statistics.fmean(float(row["log_MAE_ratio_vs_median"]) for row in eligible) if primary else "",
            "positive_family_fraction": sum(float(row["transfer_gain_vs_median"]) > 0 for row in eligible) / len(eligible) if eligible else "",
            "worst_family_gain": min((float(row["transfer_gain_vs_median"]) for row in eligible), default=""),
            "notes": "Field enters primary estimand only with at least two scorable independent families.",
        })
    primary_fields = [row for row in field_rows if row["primary_field_eligible"] == "true"]
    primary_fields.sort(key=lambda row: float(row["field_mean_transfer_gain"]), reverse=True)
    for rank, row in enumerate(primary_fields, start=1):
        row["field_rank"] = rank
    y = np.array([float(row["field_mean_transfer_gain"]) for row in primary_fields])
    groups = np.array([row["basin_id"] for row in primary_fields])
    if len(y) < 2:
        raise RuntimeError("Fewer than two primary scorable fields after unlock")
    estimate = float(np.mean(y))
    se = float(stats.sem(y))
    crit = float(stats.t.ppf(0.975, df=len(y) - 1))
    t_low, t_high = estimate - crit * se, estimate + crit * se
    fb_low, fb_high = field_bootstrap(y)
    field_frame = pd.DataFrame(primary_fields).rename(columns={"field_mean_transfer_gain": "field_mean_transfer_gain"})
    field_frame["field_mean_transfer_gain"] = field_frame["field_mean_transfer_gain"].astype(float)
    sb_low, sb_high = stratified_bootstrap(field_frame)
    wc_low, wc_high, wc_n = wild_cluster_interval(y, groups)
    hierarchical = reml_random_intercept(y, groups)

    basin_rows = []
    for basin in sorted({row["basin_id"] for row in field_rows}):
        bf = [row for row in field_rows if row["basin_id"] == basin]
        bp = [row for row in bf if row["primary_field_eligible"] == "true"]
        gains = [float(row["field_mean_transfer_gain"]) for row in bp]
        basin_rows.append({
            "basin_id": basin, "n_fields_frozen": len(bf), "n_primary_scorable_fields": len(bp),
            "n_qualified_families": sum(int(row["n_qualified_families"]) for row in bf),
            "n_scorable_families": sum(int(row["n_scorable_families"]) for row in bf),
            "field_equal_mean_transfer_gain": statistics.fmean(gains) if gains else "",
            "median_field_gain": statistics.median(gains) if gains else "",
            "positive_field_fraction": sum(value > 0 for value in gains) / len(gains) if gains else "",
            "worst_field_gain": min(gains) if gains else "",
            "interpretation_scope": "sampled replication context; no random-basin population inference",
        })

    def loo_rows(level: str) -> list[dict]:
        out = []
        keys = sorted({(row["basin_id"], row["field_id"]) if level == "field" else row["basin_id"] for row in primary_fields})
        for key in keys:
            remain = [row for row in primary_fields if ((row["basin_id"], row["field_id"]) != key if level == "field" else row["basin_id"] != key)]
            vals = np.array([float(row["field_mean_transfer_gain"]) for row in remain])
            mean = float(np.mean(vals))
            if len(vals) >= 2:
                half = float(stats.t.ppf(0.975, len(vals)-1) * stats.sem(vals))
                low, high = mean-half, mean+half
            else:
                low = high = math.nan
            item = {
                "remaining_field_count": len(vals), "field_equal_mean_transfer_gain": mean,
                "lower_CI": low, "upper_CI": high, "sign_changed": str((mean > 0) != (estimate > 0)).lower(),
                "claim_conclusion_changed": str((mean > 0) != (estimate > 0)).lower(),
            }
            if level == "field":
                item.update({"omitted_basin_id": key[0], "omitted_field_id": key[1]})
            else:
                item.update({"omitted_basin_id": key, "remaining_basin_count": len({row["basin_id"] for row in remain})})
            out.append(item)
        return out

    uncertainty_rows = [
        {"estimand":"field_equal_mean_transfer_gain","method":"small_sample_t_interval","estimate":estimate,"lower_bound":t_low,"upper_bound":t_high,"confidence_level":0.95,"n_fields":len(y),"n_basins":len(set(groups)),"headline_status":"PRIMARY"},
        {"estimand":"field_equal_mean_transfer_gain","method":"field_bootstrap_percentile","estimate":estimate,"lower_bound":fb_low,"upper_bound":fb_high,"confidence_level":0.95,"n_fields":len(y),"n_basins":len(set(groups)),"repetitions":10000,"seed":20260725,"headline_status":"ROBUSTNESS"},
        {"estimand":"field_equal_mean_transfer_gain","method":"basin_stratified_bootstrap_percentile","estimate":estimate,"lower_bound":sb_low,"upper_bound":sb_high,"confidence_level":0.95,"n_fields":len(y),"n_basins":len(set(groups)),"repetitions":10000,"seed":20260726,"headline_status":"SUPPLEMENT"},
        {"estimand":"field_equal_mean_transfer_gain","method":"wild_cluster_bootstrap_t","estimate":estimate,"lower_bound":wc_low,"upper_bound":wc_high,"confidence_level":0.95,"n_fields":len(y),"n_basins":len(set(groups)),"repetitions":wc_n,"seed":20260727,"headline_status":"SUPPLEMENT"},
        {"estimand":"field_equal_mean_transfer_gain","method":"hierarchical_REML","estimate":hierarchical["fixed_intercept"],"lower_bound":hierarchical["wald_95_low"],"upper_bound":hierarchical["wald_95_high"],"confidence_level":0.95,"n_fields":len(y),"n_basins":len(set(groups)),"headline_status":"SUPPLEMENT","notes":json.dumps(hierarchical, ensure_ascii=False)},
    ]
    candidate_rows = [
        {"stage":"frozen_qualified","count_families":len(source_map),"count_fields":len(grouped_fields),"generated_at_utc":now,"protocol_version":PROTOCOL_VERSION},
        {"stage":"numerically_scorable","count_families":len(scorable),"count_fields":len({(r['basin_id'],r['field_id']) for r in scorable}),"generated_at_utc":now,"protocol_version":PROTOCOL_VERSION},
        {"stage":"primary_scorable_fields","count_families":len(scorable),"count_fields":len(primary_fields),"generated_at_utc":now,"protocol_version":PROTOCOL_VERSION},
    ]
    diagnostic_rows = []
    detail_path = root / "registration" / "0725_source_matched_diagnostics_v1" / "0725_source_matched_diagnostic_detail_v1.csv"
    if detail_path.is_file():
        for row in read_csv(detail_path):
            diagnostic_rows.append({**row, "claim_scope": "identified source contrasts only"})
    claim_rows = [{
        "claim_id":"LAYER_D_PRIMARY","evidence_condition":"FrozenExtraTrees_vs_SourceMedian",
        "observed_result":"positive field-equal gain" if estimate > 0 else "non-positive field-equal gain",
        "allowed_wording": "Feature-conditioned ROP information transported relative to the source-only constant baseline." if estimate > 0 else "The frozen evaluation provided little, no, or negative evidence of useful external conditional transport.",
        "prohibited_wording":"Deployment readiness; future forecasting; causal optimization; random-basin population inference.",
        "scope":"sampled petroleum fields in sampled basin contexts","integrity_status":"externally timestamped access-controlled confirmation","generated_at_utc":now,
    }]
    outputs = {
        "01_candidate_flow.csv": candidate_rows, "02_family_metrics.csv": family_rows,
        "03_field_effects.csv": field_rows, "04_basin_context_summary.csv": basin_rows,
        "05_leave_one_field_out.csv": loo_rows("field"), "06_leave_one_basin_out.csv": loo_rows("basin"),
        "07_falsification_diagnostics.csv": diagnostic_rows, "08_uncertainty_summary.csv": uncertainty_rows,
        "09_claim_boundary_output.csv": claim_rows,
    }
    for name, rows_out in outputs.items():
        write_csv_from_shell(root, output, name, rows_out)
    trace.append({
        "event_id":"T3-0002","event_datetime_utc":datetime.now(timezone.utc).isoformat(),
        "actor_or_process":"run_layer_d_confirmatory.py","event_type":"SINGLE_FROZEN_EXECUTION_COMPLETE",
        "input_path":str(root / "registration" / "0726_frozen_scoring_source_map_v1.csv"),
        "input_sha256":sha256(root / "registration" / "0726_frozen_scoring_source_map_v1.csv"),
        "command_or_action":"complete cohort execution","output_path":str(output),"output_sha256":"SEE_execution_manifest.json",
        "exit_status":"PASS","protocol_version":PROTOCOL_VERSION,"notes":"All predefined outputs retained.",
    })
    write_csv_from_shell(root, output, "10_execution_trace.csv", trace)
    manifest = {
        "single_use_run_id": gate["single_use_run_id"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_manifest_sha256": sha256(root / "16_freeze_manifest.json"),
        "unlock_gate_sha256": sha256(gate_path),
        "outputs": {},
    }
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "execution_manifest.json":
            manifest["outputs"][str(path.relative_to(output)).replace("\\", "/")] = sha256(path)
    (output / "execution_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status":"PASS","primary_estimate":estimate,"n_fields":len(y),"output":str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)

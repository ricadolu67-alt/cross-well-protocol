"""Execute the frozen source-only falsification diagnostics.

This script never opens Layer D candidate archives. It uses only the seven
project-local USROP source CSVs and the already-generated historical OOF
prediction tables used for the retrospective F-15 semantic failure track.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer


PROTOCOL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "USROP"
OUTPUT_DIR = PROTOCOL_ROOT / "registration" / "0725_source_matched_diagnostics_v1"
INTERVAL_FILE = PROTOCOL_ROOT / "07a_falsification_test_intervals.csv"

FEATURES = [
    "Measured Depth m",
    "Weight on Bit kkgf",
    "Average Rotary Speed rpm",
    "Average Standpipe Pressure kPa",
]
TARGET = "Rate of Penetration m/h"
SEEDS = [20260722, 20260723, 20260724, 20260725, 20260726]
CAP_PER_UNIT = 4000
BASE_ROWS = 16000
LEAKAGE_Q = 0.05
LEAKAGE_ROWS = 800
GAP_MAX_M = 1.0
WEIGHT_CAP_M = 0.5

FAMILY_FILES = {
    "F9A": ["USROP_A 0 N-NA_F-9_Ad.csv"],
    "F14": ["USROP_A 2 N-SH_F-14d.csv"],
    "F5": ["USROP_A 5 N-SH-F-5d.csv"],
    "F15_F15S": ["USROP_A 3 N-SH-F-15d.csv", "USROP_A 4 N-SH_F-15Sd.csv"],
    "F7_F9": ["USROP_A 1 N-S_F-7d.csv", "USROP_A 6 N-SH_F-9d.csv"],
}
DEDUP_COLUMNS = FEATURES + [TARGET]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def locate_oof(name: str) -> Path:
    matches = [
        path
        for path in
        (PROJECT_ROOT / "content").glob(
            f"*/results_generated/p1_harmonized_nested_v1/predictions/{name}"
        )
        if path.parents[3].name.endswith("_v3")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one historical OOF file for {name}, found {matches}")
    return matches[0]


def read_source() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_parts: list[pd.DataFrame] = []
    for family, names in FAMILY_FILES.items():
        for name in names:
            path = DATA_DIR / name
            if not path.is_file():
                raise FileNotFoundError(path)
            frame = pd.read_csv(path, low_memory=False)
            absent = sorted(set(FEATURES + [TARGET]).difference(frame.columns))
            if absent:
                raise ValueError(f"{name}: missing {absent}")
            frame = frame.copy()
            frame["well_id"] = name
            frame["source_row"] = np.arange(len(frame), dtype=np.int64)
            frame["family"] = family
            raw_parts.append(frame)
    raw = pd.concat(raw_parts, ignore_index=True)
    for column in FEATURES + [TARGET]:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    raw = raw.replace([np.inf, -np.inf], np.nan).dropna(subset=[TARGET]).copy()

    family_parts = []
    for family in FAMILY_FILES:
        part = raw.loc[raw["family"] == family].copy()
        part = part.drop_duplicates(subset=DEDUP_COLUMNS, keep="first")
        family_parts.append(part)
    family_data = pd.concat(family_parts, ignore_index=True)
    return raw, family_data


def interval_rows(
    data: pd.DataFrame, target_file: str, start_md: float, end_md: float
) -> pd.DataFrame:
    md = data[FEATURES[0]]
    out = data.loc[
        (data["well_id"] == target_file) & (md >= start_md) & (md < end_md)
    ].copy()
    if len(out) < 2:
        raise RuntimeError(f"Insufficient test rows for {target_file}: {len(out)}")
    return out


def sample_by_unit(
    data: pd.DataFrame, unit_column: str, seed: int, cap: int = CAP_PER_UNIT
) -> pd.DataFrame:
    pieces = []
    for offset, (_, part) in enumerate(data.groupby(unit_column, sort=True)):
        take = min(cap, len(part))
        pieces.append(part.sample(n=take, replace=False, random_state=seed + offset))
    if not pieces:
        raise RuntimeError("Training sample is empty")
    return pd.concat(pieces, ignore_index=True)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, seed: int) -> np.ndarray:
    imputer = SimpleImputer(strategy="median")
    x_train = imputer.fit_transform(train[FEATURES])
    x_test = imputer.transform(test[FEATURES])
    counts = train["family"].value_counts()
    raw_weight = train["family"].map(lambda value: 1.0 / counts.loc[value]).to_numpy(float)
    weights = raw_weight / raw_weight.mean()
    model = ExtraTreesRegressor(
        n_estimators=96,
        max_depth=18,
        min_samples_leaf=100,
        max_features="sqrt",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(x_train, train[TARGET].to_numpy(float), sample_weight=weights)
    return model.predict(x_test)


def md_weighted_mae(test: pd.DataFrame, prediction: np.ndarray) -> tuple[float, float, int]:
    score = pd.DataFrame(
        {
            "md": pd.to_numeric(test[FEATURES[0]], errors="coerce").to_numpy(float),
            "observed": pd.to_numeric(test[TARGET], errors="coerce").to_numpy(float),
            "predicted": np.asarray(prediction, dtype=float),
        }
    ).dropna()
    score = score.groupby("md", as_index=False, sort=True).median(numeric_only=True)
    score["segment"] = (score["md"].diff().fillna(0) > GAP_MAX_M).cumsum()
    numerator = 0.0
    denominator = 0.0
    retained = 0
    for _, segment in score.groupby("segment", sort=True):
        segment = segment.sort_values("md")
        if len(segment) < 2:
            continue
        md = segment["md"].to_numpy(float)
        weights = np.empty(len(md), dtype=float)
        weights[0] = (md[1] - md[0]) / 2.0
        weights[-1] = (md[-1] - md[-2]) / 2.0
        if len(md) > 2:
            weights[1:-1] = (md[2:] - md[:-2]) / 2.0
        weights = np.minimum(weights, WEIGHT_CAP_M)
        valid = np.isfinite(weights) & (weights > 0)
        errors = np.abs(
            segment["observed"].to_numpy(float) - segment["predicted"].to_numpy(float)
        )
        numerator += float(np.sum(weights[valid] * errors[valid]))
        denominator += float(np.sum(weights[valid]))
        retained += int(valid.sum())
    if denominator <= 0:
        raise RuntimeError("No positive MD scoring weight")
    return numerator / denominator, denominator, retained


def split_diagnostic(
    family_data: pd.DataFrame, interval_cfg: pd.DataFrame
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in interval_cfg.loc[interval_cfg["diagnostic"] == "split"].itertuples():
        test = interval_rows(
            family_data, case.target_file, float(case.start_md_m), float(case.end_md_m)
        )
        test_keys = set(zip(test["well_id"], test["source_row"]))
        legal = family_data.loc[family_data["family"] != case.target_family].copy()
        leaky_pool = family_data.loc[family_data["family"] == case.target_family].copy()
        leaky_pool = leaky_pool.loc[
            ~pd.Series(
                list(zip(leaky_pool["well_id"], leaky_pool["source_row"])),
                index=leaky_pool.index,
            ).isin(test_keys)
        ]
        for seed in SEEDS:
            clean = sample_by_unit(legal, "family", seed)
            if len(clean) != BASE_ROWS:
                raise RuntimeError(
                    f"{case.case_id}: expected {BASE_ROWS} clean rows, got {len(clean)}"
                )
            if len(leaky_pool) < LEAKAGE_ROWS:
                raise RuntimeError(
                    f"{case.case_id}: only {len(leaky_pool)} non-test leaky rows"
                )
            rng = np.random.default_rng(seed)
            replace_pos = rng.choice(len(clean), size=LEAKAGE_ROWS, replace=False)
            leaky_add = leaky_pool.sample(
                n=LEAKAGE_ROWS, replace=False, random_state=seed
            )
            keep = np.ones(len(clean), dtype=bool)
            keep[replace_pos] = False
            leaky = pd.concat([clean.iloc[keep], leaky_add], ignore_index=True)
            pred_clean = fit_predict(clean, test, seed)
            pred_leaky = fit_predict(leaky, test, seed)
            mae_clean, coverage, n_score = md_weighted_mae(test, pred_clean)
            mae_leaky, coverage_2, n_score_2 = md_weighted_mae(test, pred_leaky)
            if coverage != coverage_2 or n_score != n_score_2:
                raise RuntimeError("Split scoring observations are not identical")
            rows.append(
                {
                    "diagnostic": "split",
                    "case_id": case.case_id,
                    "seed": seed,
                    "condition_a": "clean_family_isolation",
                    "condition_b": "row_leaky_replacement",
                    "mae_a": mae_clean,
                    "mae_b": mae_leaky,
                    "distortion_a_minus_b": mae_clean - mae_leaky,
                    "training_rows_a": len(clean),
                    "training_rows_b": len(leaky),
                    "test_rows": len(test),
                    "scoring_points": n_score,
                    "scoring_coverage_m": coverage,
                    "mechanism_isolated": True,
                    "claim_scope": "specified matched split contrast",
                }
            )
    return rows


def dependence_diagnostic(
    raw: pd.DataFrame, interval_cfg: pd.DataFrame
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in interval_cfg.loc[interval_cfg["diagnostic"] == "dependence"].itertuples():
        test = interval_rows(raw, case.target_file, float(case.start_md_m), float(case.end_md_m))
        audited_pool = raw.loc[raw["family"] != case.target_family].copy()
        nominal_pool = raw.loc[raw["well_id"] != case.target_file].copy()
        for seed in SEEDS:
            audited_operational = sample_by_unit(audited_pool, "family", seed)
            nominal_operational = sample_by_unit(nominal_pool, "well_id", seed)
            for mode, audited, nominal in [
                ("operational", audited_operational, nominal_operational),
                (
                    "matched_training_size",
                    audited_operational.sample(
                        n=min(len(audited_operational), len(nominal_operational)),
                        random_state=seed,
                    ),
                    nominal_operational.sample(
                        n=min(len(audited_operational), len(nominal_operational)),
                        random_state=seed,
                    ),
                ),
            ]:
                pred_audited = fit_predict(audited, test, seed)
                pred_nominal = fit_predict(nominal, test, seed)
                mae_audited, coverage, n_score = md_weighted_mae(test, pred_audited)
                mae_nominal, coverage_2, n_score_2 = md_weighted_mae(test, pred_nominal)
                if coverage != coverage_2 or n_score != n_score_2:
                    raise RuntimeError("Dependence scoring observations are not identical")
                rows.append(
                    {
                        "diagnostic": "dependence",
                        "case_id": case.case_id,
                        "seed": seed,
                        "condition_a": "audited_family_exclusion",
                        "condition_b": "nominal_file_exclusion",
                        "mae_a": mae_audited,
                        "mae_b": mae_nominal,
                        "distortion_a_minus_b": mae_audited - mae_nominal,
                        "training_rows_a": len(audited),
                        "training_rows_b": len(nominal),
                        "test_rows": len(test),
                        "scoring_points": n_score,
                        "scoring_coverage_m": coverage,
                        "mechanism_isolated": mode == "matched_training_size",
                        "claim_scope": f"identified dependence case; {mode}",
                    }
                )
    return rows


def retrospective_semantic_track() -> dict[str, object]:
    raw11_path = locate_oof("oof_row_raw11.csv")
    raw10_path = locate_oof("oof_row_raw10.csv")
    keys = ["row_id", "well_id", "source_row", "family", FEATURES[0], TARGET]
    raw11 = pd.read_csv(raw11_path, usecols=keys + ["prediction_Ridge"])
    raw10 = pd.read_csv(raw10_path, usecols=keys + ["prediction_Ridge"])
    raw11 = raw11.loc[raw11["well_id"] == "USROP_A 3 N-SH-F-15d.csv"].copy()
    raw10 = raw10.loc[raw10["well_id"] == "USROP_A 3 N-SH-F-15d.csv"].copy()
    merged = raw11.merge(
        raw10,
        on=keys,
        how="inner",
        validate="one_to_one",
        suffixes=("_raw11", "_raw10"),
    )
    test = merged.rename(
        columns={
            "prediction_Ridge_raw11": "released",
            "prediction_Ridge_raw10": "harmonized_proxy",
        }
    )
    mae_released, coverage, n_score = md_weighted_mae(test[keys].rename(columns={}), test["released"])
    mae_harmonized, coverage_2, n_score_2 = md_weighted_mae(
        test[keys].rename(columns={}), test["harmonized_proxy"]
    )
    if coverage != coverage_2 or n_score != n_score_2:
        raise RuntimeError("Historical semantic scoring intersection differs")
    return {
        "diagnostic": "semantics",
        "case_id": "F15_RETROSPECTIVE_RAW11_VS_RAW10_RIDGE",
        "status": "retrospective_semantic_failure_analysis",
        "confirmatory_average_bias_estimator": False,
        "rows_in_common": len(merged),
        "scoring_points": n_score,
        "scoring_coverage_m": coverage,
        "mae_released_raw11": mae_released,
        "mae_harmonized_proxy_raw10": mae_harmonized,
        "released_minus_harmonized": mae_released - mae_harmonized,
        "raw11_source": str(raw11_path.relative_to(PROJECT_ROOT)),
        "raw10_source": str(raw10_path.relative_to(PROJECT_ROOT)),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw, family_data = read_source()
    interval_cfg = pd.read_csv(INTERVAL_FILE)
    detail = pd.DataFrame(
        split_diagnostic(family_data, interval_cfg)
        + dependence_diagnostic(raw, interval_cfg)
    )
    semantic = retrospective_semantic_track()
    summary = (
        detail.groupby(["diagnostic", "case_id", "mechanism_isolated"], as_index=False)
        .agg(
            repetitions=("seed", "count"),
            mean_distortion=("distortion_a_minus_b", "mean"),
            median_distortion=("distortion_a_minus_b", "median"),
            min_distortion=("distortion_a_minus_b", "min"),
            max_distortion=("distortion_a_minus_b", "max"),
            positive_fraction=("distortion_a_minus_b", lambda x: float((x > 0).mean())),
        )
    )

    detail_path = OUTPUT_DIR / "0725_source_matched_diagnostic_detail_v1.csv"
    summary_path = OUTPUT_DIR / "0725_source_matched_diagnostic_summary_v1.csv"
    semantic_path = OUTPUT_DIR / "0725_F15_retrospective_semantic_track_v1.json"
    result_path = OUTPUT_DIR / "0725_source_matched_diagnostic_result_v1.json"
    report_path = OUTPUT_DIR / "0725_source_matched_diagnostic_report_v1.md"
    manifest_path = OUTPUT_DIR / "0725_source_matched_diagnostic_manifest_v1.json"

    detail.to_csv(detail_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    semantic_path.write_text(
        json.dumps(semantic, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    result = {
        "status": "PASS",
        "scope": "source-only; no Layer D archive opened",
        "split_rows": int((detail["diagnostic"] == "split").sum()),
        "dependence_rows": int((detail["diagnostic"] == "dependence").sum()),
        "semantic_track": "retrospective_only",
        "fixed_seeds": SEEDS,
        "leakage_fraction_q": LEAKAGE_Q,
        "leakage_rows": LEAKAGE_ROWS,
        "base_training_rows": BASE_ROWS,
    }
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report_lines = [
        "# Source-only matched falsification diagnostics",
        "",
        "- Status: `PASS`",
        "- Layer D numeric outcome access: `NONE`",
        f"- Split fits recorded: {result['split_rows']}",
        f"- Dependence fits recorded: {result['dependence_rows']}",
        "- F-15 semantic track: retrospective failure analysis only",
        "",
        "## Mean paired distortions (MAE condition A minus condition B)",
        "",
        summary.to_markdown(index=False),
        "",
        "Positive values denote the prespecified optimistic shift for split/dependence contrasts.",
        "These identified cases do not estimate a petroleum-wide average bias.",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    manifest = {
        "generated_files": {},
        "inputs": {
            str(INTERVAL_FILE.relative_to(PROTOCOL_ROOT)): sha256(INTERVAL_FILE),
            "07_falsification_diagnostics.yaml": sha256(
                PROTOCOL_ROOT / "07_falsification_diagnostics.yaml"
            ),
        },
    }
    for path in [detail_path, summary_path, semantic_path, result_path, report_path]:
        manifest["generated_files"][path.name] = sha256(path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

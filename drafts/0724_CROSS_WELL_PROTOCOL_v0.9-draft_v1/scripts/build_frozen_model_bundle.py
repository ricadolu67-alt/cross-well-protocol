from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

FEATURES = ["MD_m", "WOB_1000_kgf", "surface_RPM_rpm", "SPP_kPa"]
TARGET = "ROP_m_per_h"
GROUP = "dependence_unit"
SEEDS = [20260722, 20260723, 20260724, 20260725, 20260726]
SAMPLING_SEED = 20260722
CAP_PER_UNIT = 4000
ET_SPEC = {
    "id": "ExtraTrees_depth18_leaf100",
    "family": "ExtraTrees",
    "n_estimators": 96,
    "max_depth": 18,
    "min_samples_leaf": 100,
    "max_features": "sqrt",
}
RIDGE_SPEC = {"id": "Ridge_alpha_100", "family": "Ridge", "alpha": 100.0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("model_artifacts"))
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[3]
    legacy_root = project_root / "drafts" / "0722_跨井泛化证据链工作"
    layer_a_path = legacy_root / "0722_CROSS_WELL正式LayerA编排器_v1.py"
    inventory_path = legacy_root / "0722_CROSS_WELL源输入清单_v1.json"
    experiment_manifest_path = legacy_root / "0722_CROSS_WELL正式实验清单_v1.json"
    layer_b_transport_path = legacy_root / "0723_CROSS_WELL_LayerB传输清单_v1.json"
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite model bundle: {output_dir}")
    output_dir.mkdir(parents=True)

    experiment = json.loads(experiment_manifest_path.read_text(encoding="utf-8"))
    transport = json.loads(layer_b_transport_path.read_text(encoding="utf-8"))
    frozen_candidate = transport["candidate_specification"]
    rule = transport["transport_rule"]
    if frozen_candidate["id"] != ET_SPEC["id"]:
        raise RuntimeError("Layer B frozen candidate does not match expected ExtraTrees")
    if any(frozen_candidate.get(k) != v for k, v in ET_SPEC.items()):
        raise RuntimeError("Frozen ExtraTrees specification differs from expected values")
    if list(rule["paired_model_seeds"]) != SEEDS:
        raise RuntimeError("Frozen seed list mismatch")
    if int(rule["sampling_seed"]) != SAMPLING_SEED:
        raise RuntimeError("Frozen sampling seed mismatch")
    if int(rule["model_fit_cap_per_training_unit"]) != CAP_PER_UNIT:
        raise RuntimeError("Frozen per-unit cap mismatch")
    if rule["selected_gate_type"] != "no_gate":
        raise RuntimeError("Only the frozen NoGate learner may be exported")

    layer_a = load_module("crosswell_layer_a_artifact_export", layer_a_path)
    source, source_file_manifest = layer_a.load_source()
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    layer_a.verify_input_inventory(source, source_file_manifest, inventory)
    training = layer_a.capped_unit_sample(source, CAP_PER_UNIT, SAMPLING_SEED)

    selection = training[[GROUP, "_row_id"]].copy()
    selection.insert(0, "training_bundle_row", np.arange(len(selection), dtype=np.int64))
    selection.to_csv(output_dir / "source_training_selection.csv", index=False)

    source_median = float(np.median(source[TARGET].to_numpy(dtype=float)))
    feature_medians = {
        feature: float(training[feature].median()) for feature in FEATURES
    }
    (output_dir / "source_feature_medians.json").write_text(
        json.dumps(
            {
                "id": "FrozenSourceFeatureMedians",
                "definition": "per-feature medians from the deterministic capped 10-unit source training bundle",
                "feature_order": FEATURES,
                "values": feature_medians,
                "target_values_used": False,
                "application": "replace missing or frozen-range-invalid Layer D feature values after family qualification and before model prediction",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source_median.json").write_text(
        json.dumps(
            {
                "id": "SourceMedian",
                "value_m_per_h": source_median,
                "definition": "pooled median of all labels in the verified 10-unit Volve source queue",
                "source_rows": int(len(source)),
                "target_labels_used": "source_only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for seed in SEEDS:
        model = layer_a.fit_candidate(layer_a.build_candidate(ET_SPEC, seed), training)
        joblib.dump(model, output_dir / f"FrozenExtraTrees_seed_{seed}.joblib", compress=3)

    ridge = layer_a.fit_candidate(layer_a.build_candidate(RIDGE_SPEC, SEEDS[0]), training)
    joblib.dump(ridge, output_dir / "FrozenSourceOnlyRidge_alpha100.joblib", compress=3)

    schema = {
        "schema_version": "0.9",
        "feature_order": FEATURES,
        "canonical_units": {
            "MD_m": "m",
            "WOB_1000_kgf": "kkgf",
            "surface_RPM_rpm": "rpm",
            "SPP_kPa": "kPa",
        },
        "missing_feature_handling": "apply source_feature_medians.json before ExtraTrees prediction; Ridge contains its fitted source-only SimpleImputer",
        "target": TARGET,
        "target_unit": "m/h",
        "primary_prediction_contract": "five frozen seed-specific predictions; family loss is calculated per seed and then averaged equally across the five seeds",
    }
    (output_dir / "feature_and_prediction_schema.json").write_text(
        json.dumps(schema, indent=2) + "\n", encoding="utf-8"
    )

    artifact_names = [
        *(f"FrozenExtraTrees_seed_{seed}.joblib" for seed in SEEDS),
        "FrozenSourceOnlyRidge_alpha100.joblib",
        "source_median.json",
        "source_feature_medians.json",
        "source_training_selection.csv",
        "feature_and_prediction_schema.json",
    ]
    manifest = {
        "schema_version": "0.9",
        "status": "SOURCE_ONLY_MODEL_BUNDLE_BUILT_PENDING_V1_FREEZE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "layer_D_outcome_access": False,
        "source_scope": "verified 10-unit Volve source queue",
        "source_rows_full": int(len(source)),
        "source_units": int(source[GROUP].nunique()),
        "training_rows_after_cap": int(len(training)),
        "training_rows_per_unit": {
            str(k): int(v) for k, v in training.groupby(GROUP).size().items()
        },
        "feature_order": FEATURES,
        "ExtraTrees": ET_SPEC,
        "ExtraTrees_seeds": SEEDS,
        "NoGate": True,
        "Ridge": RIDGE_SPEC,
        "training_weighting": "family_equal",
        "sampling_seed": SAMPLING_SEED,
        "cap_per_source_unit": CAP_PER_UNIT,
        "source_median_m_per_h": source_median,
        "source_feature_medians": feature_medians,
        "source_inventory_path": "../0722_跨井泛化证据链工作/0722_CROSS_WELL源输入清单_v1.json",
        "source_inventory_sha256": sha256(inventory_path),
        "experiment_manifest_sha256": sha256(experiment_manifest_path),
        "layer_B_transport_manifest_sha256": sha256(layer_b_transport_path),
        "layer_A_orchestrator_sha256": sha256(layer_a_path),
        "export_script_sha256": sha256(Path(__file__).resolve()),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "artifacts": [
            {
                "path": name,
                "bytes": (output_dir / name).stat().st_size,
                "sha256": sha256(output_dir / name),
            }
            for name in artifact_names
        ],
    }
    (output_dir / "model_bundle_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "source_rows": len(source),
        "source_units": int(source[GROUP].nunique()),
        "training_rows": len(training),
        "models": 6,
        "output": str(output_dir),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

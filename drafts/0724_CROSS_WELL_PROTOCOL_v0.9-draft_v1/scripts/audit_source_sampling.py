from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

MD = "Measured Depth m"
WOB = "Weight on Bit kkgf"
RPM = "Average Rotary Speed rpm"
SPP = "Average Standpipe Pressure kPa"
ROP = "Rate of Penetration m/h"
REQUIRED = [MD, WOB, RPM, SPP, ROP]
G_MAX_M = 1.0
W_MAX_M = 0.5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def q(values: np.ndarray, probability: float) -> float | None:
    values = values[np.isfinite(values)]
    return None if values.size == 0 else float(np.quantile(values, probability))


def segment_unique_md(md: np.ndarray) -> list[np.ndarray]:
    segments: list[list[float]] = []
    current: list[float] = []
    previous: float | None = None
    for value in md:
        if not np.isfinite(value):
            if current:
                segments.append(current)
                current = []
            previous = None
            continue
        if previous is not None and (value < previous or value - previous > G_MAX_M):
            if current:
                segments.append(current)
            current = []
        current.append(float(value))
        previous = float(value)
    if current:
        segments.append(current)
    return [np.unique(np.asarray(x, dtype=float)) for x in segments]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("../../data/USROP"))
    parser.add_argument("--output-dir", type=Path, default=Path("source_only_audit"))
    args = parser.parse_args()
    source_root_arg = args.source_root
    source_root = source_root_arg.resolve()
    source_root_logical = source_root_arg.as_posix()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(source_root.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files under {source_root}")

    file_rows: list[dict] = []
    segment_rows: list[dict] = []
    all_positive_gaps: list[float] = []
    input_rows: list[dict] = []

    for path in files:
        input_rows.append(
            {
                "path": f"{source_root_logical.rstrip('/')}/{path.name}",
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
        frame = pd.read_csv(path, usecols=REQUIRED)
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        md = numeric[MD].to_numpy(dtype=float)
        delta = np.diff(md)
        positive = delta[np.isfinite(delta) & (delta > 0)]
        all_positive_gaps.extend(positive.tolist())
        segments = segment_unique_md(md)
        for index, values in enumerate(segments, start=1):
            span = float(values[-1] - values[0]) if values.size >= 2 else 0.0
            segment_rows.append(
                {
                    "source_file": path.name,
                    "segment_id": index,
                    "unique_MD_points": int(values.size),
                    "MD_start_m": float(values[0]),
                    "MD_end_m": float(values[-1]),
                    "MD_span_m": span,
                    "meets_two_point_minimum": str(values.size >= 2).lower(),
                }
            )
        row = {
            "source_file": path.name,
            "rows": len(frame),
            "MD_min_m": float(np.nanmin(md)),
            "MD_max_m": float(np.nanmax(md)),
            "positive_MD_span_sum_m": float(np.sum(positive)),
            "duplicate_MD_steps": int(np.sum(delta == 0)),
            "decreasing_MD_steps": int(np.sum(np.isfinite(delta) & (delta < 0))),
            "gaps_gt_1m": int(np.sum(positive > G_MAX_M)),
            "segments_at_1m_gap": len(segments),
            "valid_segment_span_sum_m": float(
                sum((x[-1] - x[0]) if x.size >= 2 else 0.0 for x in segments)
            ),
            "ROP_nonpositive_count": int((numeric[ROP] <= 0).sum()),
        }
        for name, prefix in [(MD, "MD"), (WOB, "WOB"), (RPM, "RPM"), (SPP, "SPP"), (ROP, "ROP")]:
            x = numeric[name].to_numpy(dtype=float)
            row[f"{prefix}_missing_fraction"] = float(np.mean(np.isnan(x)))
            row[f"{prefix}_finite_fraction"] = float(np.mean(np.isfinite(x)))
            row[f"{prefix}_minimum"] = float(np.nanmin(x))
            row[f"{prefix}_maximum"] = float(np.nanmax(x))
        file_rows.append(row)

    gaps = np.asarray(all_positive_gaps, dtype=float)
    quantile_rows = [
        {"quantity": "positive_consecutive_MD_gap_m", "quantile": label, "value": q(gaps, probability)}
        for label, probability in [
            ("min", 0.0), ("p50", 0.5), ("p90", 0.9), ("p95", 0.95),
            ("p99", 0.99), ("p995", 0.995), ("p999", 0.999), ("max", 1.0)
        ]
    ]

    pd.DataFrame(file_rows).to_csv(output_dir / "source_sampling_file_audit.csv", index=False)
    pd.DataFrame(segment_rows).to_csv(output_dir / "source_sampling_segment_audit.csv", index=False)
    pd.DataFrame(quantile_rows).to_csv(output_dir / "source_sampling_quantiles.csv", index=False)
    pd.DataFrame(input_rows).to_csv(output_dir / "source_input_hashes.csv", index=False)

    valid_spans = np.asarray([r["MD_span_m"] for r in segment_rows if r["unique_MD_points"] >= 2])
    report = f"""# Source-only Measurement Alignment and Sampling Audit

Generated: {datetime.now(timezone.utc).isoformat()}

## Scope

- Source logical path: `{source_root_logical}`
- Files: {len(files)}
- Rows: {sum(r['rows'] for r in file_rows):,}
- Layer D outcome access: none
- Required columns: {", ".join(REQUIRED)}

## Sampling geometry

- Positive consecutive MD gaps: {gaps.size:,}
- Median gap: {q(gaps, 0.5):.6f} m
- 99th percentile: {q(gaps, 0.99):.6f} m
- 99.9th percentile: {q(gaps, 0.999):.6f} m
- Maximum: {q(gaps, 1.0):.6f} m
- Gaps greater than 1.0 m: {int(np.sum(gaps > 1.0))}
- Segments under the frozen 1.0 m break rule: {len(segment_rows)}
- Valid segment span median: {q(valid_spans, 0.5):.3f} m

## Frozen parameter basis

1. `g_max = 1.0 m`. This is above the source 99.9th-percentile native gap
   while breaking the sparse large discontinuities instead of assigning them
   depth weight.
2. `w_max = 0.5 m`. This bounds any single native record's representative
   interval to half of the segment-breaking gap and prevents endpoint or
   locally sparse records from dominating the loss.
3. Minimum segment size is two unique MD points, the minimum needed to define
   a positive represented interval.
4. Minimum family scoring coverage is 100 m, with at least 100 scoring points
   and one valid segment. These are engineering precision/coverage guards,
   not model-performance thresholds.
5. Fixed-depth sensitivity uses 1.0 m blocks anchored at 0.0 m, requires at
   least 0.5 m represented coverage per block, and introduces no interpolation.
6. Native co-sampled rows are the primary alignment unit. Cross-file fuzzy
   matching, time joins, and pre-prediction resampling are excluded.

## ROP semantic observations

- Source ROP missing/non-finite values are reported in the file audit.
- Non-positive source ROP count: {sum(r['ROP_nonpositive_count'] for r in file_rows)}.
- No upper ROP threshold was selected from source outcomes; the primary
  protocol retains finite positive extremes and reports them.

These choices were made without Layer D ROP or performance feedback.
"""
    (output_dir / "source_only_parameter_basis.md").write_text(report, encoding="utf-8")

    generated = [
        "source_sampling_file_audit.csv",
        "source_sampling_segment_audit.csv",
        "source_sampling_quantiles.csv",
        "source_input_hashes.csv",
        "source_only_parameter_basis.md",
    ]
    manifest = {
        "schema_version": "0.9",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_only": True,
        "layer_D_outcome_access": False,
        "source_root_logical": source_root_logical,
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "script_sha256": sha256(Path(__file__).resolve()),
        "parameters": {"g_max_m": G_MAX_M, "w_max_m": W_MAX_M},
        "input_files": input_rows,
        "outputs": [
            {"path": name, "sha256": sha256(output_dir / name)} for name in generated
        ],
    }
    (output_dir / "source_sampling_audit_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "files": len(files),
        "rows": sum(r["rows"] for r in file_rows),
        "segments": len(segment_rows),
        "gap_p999_m": q(gaps, 0.999),
        "gaps_gt_1m": int(np.sum(gaps > 1.0)),
        "output": str(output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()

"""Reproduce headline CROSS-WELL Layer D summaries from derived field effects."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent
INPUT = HERE / "headline_field_effects.csv"
HASH_FILE = HERE / "headline_field_effects.sha256"
GENERATED = HERE / "generated"
T_CRITICAL_DF7_975 = 2.3646242515927836


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_input() -> str:
    expected = HASH_FILE.read_text(encoding="utf-8").split()[0].lower()
    observed = sha256(INPUT)
    if expected != observed:
        raise SystemExit(f"SHA-256 mismatch: expected {expected}, observed {observed}")
    return observed


def load_rows() -> list[dict[str, str]]:
    with INPUT.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 8:
        raise SystemExit(f"Expected 8 primary fields; found {len(rows)}")
    gorgon = next(row for row in rows if row["field"] == "Gorgon")
    if int(gorgon["scorable_families"]) != 3:
        raise SystemExit("Gorgon audit failed: expected 3 scorable families")
    return rows


def make_svg(rows: list[dict[str, str]], mean: float, lower: float, upper: float) -> str:
    width, height = 820, 470
    left, right, top, bottom = 190, 35, 45, 65
    values = [float(row["field_transfer_gain_m_per_h"]) for row in rows]
    x_min, x_max = 0.0, max(4.2, max(values) + 0.3)

    def x(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * (width - left - right)

    ordered = sorted(rows, key=lambda row: float(row["field_transfer_gain_m_per_h"]))
    step = (height - top - bottom) / (len(ordered) + 1)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.label{font-size:14px}.small{font-size:12px}.title{font-size:18px;font-weight:700}</style>',
        '<text x="410" y="25" text-anchor="middle" class="title">Layer D field-level Transfer Gain</text>',
        f'<line x1="{x(0):.1f}" y1="{top}" x2="{x(0):.1f}" y2="{height-bottom}" stroke="#777" stroke-dasharray="4,4"/>',
    ]
    for tick in range(5):
        xpos = x(float(tick))
        lines.append(f'<line x1="{xpos:.1f}" y1="{height-bottom}" x2="{xpos:.1f}" y2="{height-bottom+6}" stroke="#222"/>')
        lines.append(f'<text x="{xpos:.1f}" y="{height-bottom+24}" text-anchor="middle" class="small">{tick}</text>')
    for index, row in enumerate(ordered, start=1):
        y = top + index * step
        gain = float(row["field_transfer_gain_m_per_h"])
        lines.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" class="label">{row["field"]}</text>')
        lines.append(f'<circle cx="{x(gain):.1f}" cy="{y:.1f}" r="5" fill="#1f77b4"/>')
        lines.append(f'<text x="{x(gain)+10:.1f}" y="{y+5:.1f}" class="small">+{gain:.3f}</text>')
    y = top + (len(ordered) + 1) * step
    lines.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" class="label" font-weight="700">Field-equal mean</text>')
    lines.append(f'<line x1="{x(lower):.1f}" y1="{y:.1f}" x2="{x(upper):.1f}" y2="{y:.1f}" stroke="#b22222" stroke-width="3"/>')
    lines.append(f'<polygon points="{x(mean):.1f},{y-8:.1f} {x(mean)+8:.1f},{y:.1f} {x(mean):.1f},{y+8:.1f} {x(mean)-8:.1f},{y:.1f}" fill="#b22222"/>')
    lines.append(f'<text x="{(left+width-right)/2:.1f}" y="{height-12}" text-anchor="middle" class="label">SourceMedian-relative Transfer Gain (m/h)</text>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    input_hash = verify_input()
    rows = load_rows()
    gains = [float(row["field_transfer_gain_m_per_h"]) for row in rows]
    log_ratios = [float(row["field_mean_family_log_MAE_ratio"]) for row in rows]
    mean = statistics.fmean(gains)
    standard_error = statistics.stdev(gains) / math.sqrt(len(gains))
    lower = mean - T_CRITICAL_DF7_975 * standard_error
    upper = mean + T_CRITICAL_DF7_975 * standard_error
    log_mean = statistics.fmean(log_ratios)
    expected = (2.07186853190208, 1.0248606156868203, 3.11887644811734, -0.09307030943604601)
    observed = (mean, lower, upper, log_mean)
    if any(not math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12) for a, b in zip(observed, expected, strict=True)):
        raise SystemExit(f"Headline audit failed: {observed}")
    GENERATED.mkdir(exist_ok=True)
    summary = {
        "status": "PASS",
        "source_sha256": input_hash,
        "primary_fields": len(rows),
        "positive_field_fraction": sum(value > 0 for value in gains) / len(gains),
        "field_equal_transfer_gain_m_per_h": mean,
        "small_sample_t_interval_95": [lower, upper],
        "family_then_field_equal_log_MAE_ratio": log_mean,
        "geometric_ratio_reduction_percent": 100.0 * (1.0 - math.exp(log_mean)),
        "gorgon_scorable_families": 3,
        "scope": "post-unlock derived-data reproduction; frozen protocol release unchanged",
    }
    (GENERATED / "headline_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (GENERATED / "headline_field_effects.svg").write_text(make_svg(rows, mean, lower, upper), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("REPRODUCTION: PASS")


if __name__ == "__main__":
    main()

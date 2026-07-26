"""Synthetic validation of every frozen uncertainty-analysis branch."""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats


PROTOCOL_ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    PROTOCOL_ROOT
    / "registration"
    / "0725_synthetic_full_dry_run_v1"
    / "outputs"
    / "03_field_effects.csv"
)
OUTPUT = PROTOCOL_ROOT / "registration" / "0725_uncertainty_plan_test_v1"
VALUE = "field_mean_transfer_gain"
GROUP = "basin_id"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def t_interval(y: np.ndarray) -> tuple[float, float, float]:
    mean = float(np.mean(y))
    se = float(stats.sem(y))
    crit = float(stats.t.ppf(0.975, df=len(y) - 1))
    return mean, mean - crit * se, mean + crit * se


def percentile_interval(values: np.ndarray) -> tuple[float, float]:
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def field_bootstrap(y: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(20260725)
    draws = np.empty(10000)
    for index in range(len(draws)):
        draws[index] = np.mean(rng.choice(y, size=len(y), replace=True))
    return percentile_interval(draws)


def stratified_bootstrap(frame: pd.DataFrame) -> tuple[float, float]:
    rng = np.random.default_rng(20260726)
    groups = [part[VALUE].to_numpy(float) for _, part in frame.groupby(GROUP, sort=True)]
    draws = np.empty(10000)
    for index in range(len(draws)):
        sampled = [rng.choice(values, size=len(values), replace=True) for values in groups]
        draws[index] = np.mean(np.concatenate(sampled))
    return percentile_interval(draws)


def cluster_se(y: np.ndarray, group: np.ndarray) -> float:
    residual = y - np.mean(y)
    scores = np.array([residual[group == item].sum() for item in np.unique(group)])
    clusters = len(scores)
    if clusters < 2:
        return float("nan")
    variance = (clusters / (clusters - 1.0)) * np.sum(scores**2) / (len(y) ** 2)
    return float(np.sqrt(max(variance, 0.0)))


def wild_cluster_interval(y: np.ndarray, group: np.ndarray) -> tuple[float, float, int]:
    rng = np.random.default_rng(20260727)
    beta = float(np.mean(y))
    residual = y - beta
    se = cluster_se(y, group)
    unique = np.unique(group)
    t_values = []
    for _ in range(9999):
        weights = dict(zip(unique, rng.choice([-1.0, 1.0], size=len(unique))))
        y_star = beta + np.array([weights[item] for item in group]) * residual
        se_star = cluster_se(y_star, group)
        if np.isfinite(se_star) and se_star > 0:
            t_values.append((float(np.mean(y_star)) - beta) / se_star)
    if len(t_values) < 9000:
        raise RuntimeError(f"Only {len(t_values)} valid wild-bootstrap replicates")
    q_low, q_high = np.quantile(t_values, [0.025, 0.975])
    return float(beta - q_high * se), float(beta - q_low * se), len(t_values)


def reml_random_intercept(y: np.ndarray, group: np.ndarray) -> dict[str, object]:
    unique = np.unique(group)
    z = np.column_stack([(group == item).astype(float) for item in unique])
    x = np.ones((len(y), 1), dtype=float)

    def objective(theta: np.ndarray) -> float:
        tau2, sigma2 = np.exp(theta)
        v = tau2 * (z @ z.T) + sigma2 * np.eye(len(y))
        sign_v, logdet_v = np.linalg.slogdet(v)
        if sign_v <= 0:
            return float("inf")
        vinv = np.linalg.inv(v)
        xt_vinv_x = x.T @ vinv @ x
        sign_x, logdet_x = np.linalg.slogdet(xt_vinv_x)
        if sign_x <= 0:
            return float("inf")
        beta = np.linalg.solve(xt_vinv_x, x.T @ vinv @ y)
        resid = y - x @ beta
        quad = float(resid.T @ vinv @ resid)
        return 0.5 * (
            (len(y) - 1) * np.log(2.0 * np.pi) + logdet_v + logdet_x + quad
        )

    variance = max(float(np.var(y, ddof=1)), 1e-8)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fitted = optimize.minimize(
            objective,
            x0=np.log([variance / 2.0, variance / 2.0]),
            method="L-BFGS-B",
            bounds=[(-20.0, 20.0), (-20.0, 20.0)],
        )
    tau2, sigma2 = np.exp(fitted.x)
    v = tau2 * (z @ z.T) + sigma2 * np.eye(len(y))
    vinv = np.linalg.inv(v)
    information = x.T @ vinv @ x
    beta = float(np.linalg.solve(information, x.T @ vinv @ y)[0])
    se = float(np.sqrt(np.linalg.inv(information)[0, 0]))
    return {
        "converged": bool(fitted.success),
        "optimizer_message": str(fitted.message),
        "fixed_intercept": beta,
        "standard_error": se,
        "wald_95_low": beta - 1.959963984540054 * se,
        "wald_95_high": beta + 1.959963984540054 * se,
        "between_basin_variance": float(tau2),
        "residual_variance": float(sigma2),
        "singular_boundary_flag": bool(tau2 < 1e-7 or sigma2 < 1e-7),
        "warnings": [str(item.message) for item in caught],
    }


def main() -> int:
    frame = pd.read_csv(INPUT)
    frame = frame.loc[frame["primary_field_eligible"].astype(bool)].copy()
    y = frame[VALUE].to_numpy(float)
    group = frame[GROUP].astype(str).to_numpy()
    mean, t_low, t_high = t_interval(y)
    fb_low, fb_high = field_bootstrap(y)
    sb_low, sb_high = stratified_bootstrap(frame)
    wc_low, wc_high, wc_valid = wild_cluster_interval(y, group)
    hierarchical = reml_random_intercept(y, group)
    result = {
        "status": "PASS" if hierarchical["converged"] else "FAIL",
        "scope": "synthetic dry-run field effects only",
        "n_fields": len(y),
        "n_basins": len(np.unique(group)),
        "field_equal_mean": mean,
        "small_sample_t_interval": [t_low, t_high],
        "field_bootstrap_percentile_interval": [fb_low, fb_high],
        "basin_stratified_bootstrap_percentile_interval": [sb_low, sb_high],
        "wild_cluster_bootstrap_t_interval": [wc_low, wc_high],
        "wild_cluster_valid_repetitions": wc_valid,
        "hierarchical_REML": hierarchical,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT / "0725_uncertainty_plan_test_result_v1.json"
    report_path = OUTPUT / "0725_uncertainty_plan_test_report_v1.md"
    manifest_path = OUTPUT / "0725_uncertainty_plan_test_manifest_v1.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = [
        "# Uncertainty plan synthetic validation",
        "",
        f"- Status: `{result['status']}`",
        "- Scope: synthetic field effects only; no Layer D outcomes",
        f"- Fields / basin contexts: {len(y)} / {len(np.unique(group))}",
        f"- Field-equal mean: {mean:.6f}",
        f"- Small-sample t interval: [{t_low:.6f}, {t_high:.6f}]",
        f"- Field bootstrap: [{fb_low:.6f}, {fb_high:.6f}]",
        f"- Basin-stratified bootstrap: [{sb_low:.6f}, {sb_high:.6f}]",
        f"- Wild-cluster bootstrap-t: [{wc_low:.6f}, {wc_high:.6f}]",
        f"- REML converged: {hierarchical['converged']}",
        "",
        "All supplementary methods remain subordinate to the complete field table",
        "and the prespecified small-sample t interval.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "inputs": {
            str(INPUT.relative_to(PROTOCOL_ROOT)): sha256(INPUT),
            "10_uncertainty_plan.yaml": sha256(PROTOCOL_ROOT / "10_uncertainty_plan.yaml"),
        },
        "generated_files": {
            result_path.name: sha256(result_path),
            report_path.name: sha256(report_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

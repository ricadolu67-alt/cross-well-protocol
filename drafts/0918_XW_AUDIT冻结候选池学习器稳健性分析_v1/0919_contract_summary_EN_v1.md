# English summary: post-unlock frozen-candidate-pool learner-robustness contract (v1)

> This is an English summary for readers who do not read Chinese. The binding text is the Chinese contract
> `0918_冻结候选池稳健性分析合同_v1.md` in this folder (SHA-256
> `1178946d54b43964435807d8613d0c93b258ce4a8f7d8be18a84fd7d9372efb7`), fixed by the signed tag
> [`xw-audit-learner-pool-contract-v1`](https://github.com/ricadolu67-alt/cross-well-protocol/tree/xw-audit-learner-pool-contract-v1).
> Where this summary and the contract differ, the contract governs.
>
> Updated status (2026-09-19): **analysis completed under v1 plus the signed v2 loader-location amendment**. The earlier status was “not yet executed”; the original v1 contract remains unchanged. The v2 amendment is fixed by [`xw-audit-learner-pool-contract-v2`](https://github.com/ricadolu67-alt/cross-well-protocol/tree/xw-audit-learner-pool-contract-v2), commit `2ef0f3a675e0eec2c4b91810041dc8e7da9a3a9a`.

## 1. Identity

**Post-unlock, contract-fixed, exploratory learner-robustness analysis of the frozen Layer A candidate pool.**

- It is not a new confirmatory evaluation and does not restore prospective model comparison.
- It does not replace or upgrade the registered primary estimand (field-equal Transfer Gain of the frozen ExtraTrees model relative to the SourceMedian constant).
- The eight candidate **configurations** were frozen in the formal Layer A manifest before Layer D outcome access. The **decision** to score all eight on Layer D was made after Layer D outcomes were known. The tag constrains later analyst choices; it does not make this comparison outcome-naive.

## 2. Single question

> Does the conclusion that strong cross-field incremental predictive value is difficult to establish under the common4-SPP information set depend materially on the choice of the frozen ExtraTrees model within the pre-Layer-D frozen candidate pool?

Out of scope: learner families that were never in the frozen pool (random forest, XGBoost, SVR, sequence models, physics-based ROP equations).

## 3. Candidates (the complete frozen pool, nothing added or removed)

| Candidate | Family | Frozen configuration | Handling |
|---|---|---|---|
| `ExtraTrees_depth18_leaf100` | ExtraTrees | 96 trees, depth 18, min leaf 100, sqrt features | Frozen models reused (the registered primary learner) |
| `Ridge_alpha_100` | Ridge | alpha 100 | Frozen model reused (the registered comparator) |
| `ExtraTrees_depth12_leaf30` | ExtraTrees | 96 trees, depth 12, min leaf 30, sqrt features | Refitted, 5 seeds |
| `HistGB_lr005_leaf15` | HistGradientBoosting | 180 iterations, lr 0.05, 15 leaves, min leaf 60, L2 1.0 | Refitted, 5 seeds |
| `HistGB_lr008_leaf31` | HistGradientBoosting | 180 iterations, lr 0.08, 31 leaves, min leaf 60, L2 1.0 | Refitted, 5 seeds |
| `MLP_64_32` | MLP | (64, 32), alpha 1e-3, batch 512, lr 1e-3, early stopping, validation 0.15, max 80 iterations | Refitted, 5 seeds |
| `MLP_96_48` | MLP | (96, 48), otherwise as above | Refitted, 5 seeds |
| `Ridge_alpha_1` | Ridge | alpha 1 | Refitted once (deterministic) |

Comparators outside the pool: the registered SourceMedian constant (22.6289616 m/h) and the previously fitted MD-only Ridge.

## 4. Training rules

- Inputs: measured depth, weight on bit, surface RPM, standpipe pressure. Target: ROP.
- Exactly the 36,779 source training rows, in the same order, used to build the frozen models; no resampling.
- The same build and fit functions, family-equal sample weights and seeds (20260722–20260726) as the frozen models.
- Missing-value rule: tree models receive frozen source feature medians before prediction; pipeline models (Ridge, MLP) use their own fitted imputer. **This harmonized preprocessing rule was fixed post-unlock, before scoring; it was not part of the frozen pool.** HistGB results must therefore be described as a frozen configuration evaluated under post-unlock harmonized preprocessing.
- No tuning, grid search, early-stopping changes, target-domain fitting or calibration. No candidate may be dropped, replaced or rerun because of its Layer D result.

## 5. Guards before any new candidate is scored

- Refit `ExtraTrees_depth18_leaf100` (seed 20260722) and `Ridge_alpha_100` through the same path; their Layer D predictions must match the frozen models within an absolute difference of 1e-10.
- The registered results must also reproduce: 23 qualified, 21 scorable and 19 primary families in 8 primary fields; Transfer Gain 2.07186853190208 m/h; 95% t interval [1.0248606, 3.1188764].
- If any guard fails, scoring stops before any new-candidate prediction is produced. The tolerance may not be relaxed; a fix requires a new contract version and a full restart.
- Convergence warnings (for example for the MLP) are recorded as they occur; no rerun, seed change or iteration change is allowed.

## 6. Scoring and reporting

- The registered Layer D scoring function is reused unchanged: MD-interval weights capped at 0.5 m, segments broken at gaps above 1.0 m, family eligibility of at least 100 m coverage and 100 scoring points, and primary fields with at least two scorable families. Families are equal within field; the 8 primary fields are equal.
- For each of the 8 candidates, three fixed contrasts (positive favours the candidate): versus MD-only Ridge (**focal**), versus SourceMedian, and versus the frozen ExtraTrees.
- Each contrast reports the 8-field equal mean, a 95% small-sample t interval, the number of positive fields out of 8, and all 8 leave-one-field-out estimates. Intervals are descriptive and exploratory; no multiplicity correction and no confirmatory p-values. The field is the independent unit.

## 7. Pre-specified reading rules

Three independent descriptions, never merged into one pass/fail label:

1. **Field-equal mean advantage**: the lower bound of the 95% t interval is greater than zero.
2. **Directional consistency**: positive fields reported as x/8; the phrase "directionally consistent across most fields" is allowed only for x ≥ 6, which is a descriptive requirement, not a second inferential test.
3. **Single-field robustness**: whether all leave-one-field-out estimates keep the full-sample sign.

All results for all eight candidates are reported whatever they show. Prohibited conclusions include "complexity does not provide transferable value", "neural networks do not transfer" and "ExtraTrees is the best learner for ROP". MLP results may only be described as results for "the two frozen MLP configurations".

## 8. Inputs and access

The contract locks 19 inputs by SHA-256. Some of them (the locked Layer D results package, which contains row-level values derived from NOPIMS archives, and several source-side working files) are not redistributed in this repository; their hashes allow verification when the files are provided to reviewers or reproducers.

## 9. Amendment and execution history

The v2 amendment binds the production source loader to its original exact path and SHA-256. Every same-named file under drafts/ is inventoried: identical copies are recorded and permitted; different contents, unreadable files or an incomplete scan stop execution. Only the original path is imported. Both contract tags and file hashes are verified before source loading. The amendment SHA-256 is `59153449679a8d7b2a3de7e7f3c9f4262f6f3f7c47e09c702d79f45d928286b2`.

The original duplicate-copy stop was preserved. A subsequent implementation error used `md` as the MD-only prediction key, colliding with the unchanged scoring function's reserved depth key. The original-result guard detected the mismatch before any new candidate was scored. The key was corrected to `md_only_ridge`, all guards were rerun, and all passed. Neither the scoring function nor the tolerance was changed.

The first report contained floating-point residue in the frozen ExtraTrees self-comparison. Reporting successor v2 reuses the same aggregated candidate losses for the frozen-ExtraTrees comparator, making self-comparison exactly zero. The maximum field-effect change was 2.132e-14 m/h; no additional fitting or prediction was performed. Earlier tables and execution records are retained. The v2 report and tables are the current reporting versions.

## 10. Completed exploratory results

All eight candidates and all three fixed contrasts were reported: 736 candidate-seed-family rows, 192 field contrasts, 24 contrast summaries and 192 leave-one-field-out estimates.

- No candidate established a positive field-equal mean advantage over MD-only Ridge: all eight point estimates were negative and none had a positive lower 95% t bound. This is not an equivalence result or evidence that operational variables have no physical effect.
- Only the two ExtraTrees configurations had a positive lower t bound against SourceMedian. The registered depth18/leaf100 configuration had a gain of 2.071869 m/h [1.024861, 3.118876], with 8/8 positive fields; depth12/leaf30 had 1.826042 [0.748837, 2.903247], with 7/8 positive fields. Both retained positive leave-one-field-out estimates.
- All seven other configurations had negative mean gains against the frozen ExtraTrees comparator. This is limited to the fixed candidate pool and the observed cohort, not a claim of general learner superiority.
- Both MLP configurations issued ConvergenceWarning for all five seeds at the frozen 80-iteration limit. These warnings appear in every affected reporting row; seeds and iteration limits were not changed. The results describe the two frozen configurations, not neural networks generally.

Source-versus-Layer-D rankings were positively associated: descriptive Spearman correlations were 0.904762 for mean outer-fold worst-2 ranks and 0.886243 for mean outer-fold mean-MAE ranks. Full per-outer-fold source ranks are retained. No rank-based reselection was performed.

All specified pre-scoring guards and the final report recomputation passed. Technical checks do not constitute independent scientific acceptance. The [derived-results package](publication_v1/README.md) provides the current comparison tables, fitting diagnostics, report and a standard-library reproduction script. It reproduces derived field-table calculations rather than the full training and raw-data scoring pipeline.

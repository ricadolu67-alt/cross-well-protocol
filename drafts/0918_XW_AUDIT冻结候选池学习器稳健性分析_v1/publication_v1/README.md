# Does model choice change the cross-field ROP conclusion?

This package compares eight fixed model configurations across eight oilfields to examine how model choice affects conclusions about rate-of-penetration (ROP) prediction. It contains the completed frozen-candidate-pool analysis for XW-AUDIT.

The candidate configurations were frozen before Layer D outcomes were examined. **This comparison was planned after those outcomes were known and is exploratory.** It does not replace the registered primary analysis.

## What did the comparison show?

| Comparison | Finding across the eight candidates |
|---|---|
| Against Ridge using measured depth (MD) alone | No candidate established a positive oilfield-equal mean advantage; all eight mean differences were negative. |
| Against SourceMedian, a constant prediction based on source-data ROP | Only the two ExtraTrees configurations had a positive lower bound for the descriptive 95% t interval. |

The advantage over a constant baseline therefore did not establish an advantage over a depth-only model. This does not demonstrate model equivalence, rule out physical effects of operating parameters, or establish general ExtraTrees superiority.

**Both MLP configurations reached the fixed 80-iteration limit with convergence warnings for all five seeds each.** These findings concern the tested configurations, not neural networks generally. HistGB also used post-unlock harmonized preprocessing; its complete pipeline was not frozen before outcomes were known.

Read the [full report in Chinese](results_ZH.md) or inspect the [24 comparison summaries](contrast_summary.csv). Positive differences favour the candidate; the summaries weight each oilfield equally. Intervals are exploratory and do not support multiplicity-adjusted or confirmatory claims.

## Reproduce the summary calculations

With Python 3, run from this directory:

```text
python reproduce_pool.py
```

No additional packages are required. A successful run prints:

```json
{"status": "PASS_DERIVED_FIELD_TABLE_REPRODUCTION", "contrasts": 24, "field_effects": 192, "LOFO": 192, "MLP_warning_seeds": 10}
```

The script checks file hashes and recalculates the means, intervals and leave-one-field-out (LOFO) summaries from the supplied oilfield-level tables. It also checks the recorded MLP warnings. **Passing verifies these derived calculations; it does not rerun model training or independently validate the underlying data or scientific interpretation.**

## Find the supporting material

| Material | Files |
|---|---|
| Results and uncertainty | [Oilfield effects](field_effects.csv), [comparison summaries](contrast_summary.csv), [leave-one-field-out estimates](leave_one_field_out.csv) |
| Source-to-target rankings | [Rank comparison](source_target_ranks.csv), [source outer-fold ranks](source_outer_fold_ranks.csv) |
| Model fitting | [Diagnostics for the 26 new fits](fit_diagnostics.csv) |
| Interpretation | [Full report](results_ZH.md) |
| Reproduction and provenance | [Reproduction script](reproduce_pool.py), [file hashes and source mapping](manifest.json), [contracts and execution notes](execution_notes.md) |

The package contains derived results. Raw ROP records, individual predictions and fitted models are not included. Execution notes explain the signed contracts, preserved failure records, reporting corrections and numerical checks.

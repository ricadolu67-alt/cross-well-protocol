# Contracts, execution history and reproduction details

See the [README](README.md) for the research question, findings and quick start.

## Evidence status and scope

This is the completed B first-layer analysis: eight pre-Layer-D frozen candidate configurations evaluated under a post-unlock contract. It is not outcome-naive and does not replace the registered primary estimand. HistGB configurations use post-unlock harmonized source-median preprocessing, not a pre-outcome frozen HistGB pipeline.

Both frozen MLP configurations reached the fixed 80-iteration limit with ConvergenceWarning for all five seeds. No seed, iteration limit or learning rate was changed. The fit diagnostics cover 26 new candidate-seed fits; reused frozen models are not newly fitted entries in that table.

## Contract and execution history


- Original contract: [signed v1](https://github.com/ricadolu67-alt/cross-well-protocol/tree/xw-audit-learner-pool-contract-v1).
- Loader-location amendment: [signed v2](https://github.com/ricadolu67-alt/cross-well-protocol/tree/xw-audit-learner-pool-contract-v2), commit `2ef0f3a675e0eec2c4b91810041dc8e7da9a3a9a`.
- The first stop concerned an identical loader copy in a reproduction package; v2 binds the original path and hash while inventorying all copies.
- A subsequent implementation used prediction key `md`, colliding with the frozen scorer's depth key. The original-result guard stopped execution before new-candidate prediction. The key was corrected, and all guards were rerun successfully without changing the frozen scorer or tolerance.
- Reporting successor v2 removes floating-point residue from the ET self-comparison by reusing the same candidate loss aggregate as its comparator; the maximum field-effect change was 2.132e-14 m/h. No refit or new prediction was involved. All affected tables explicitly retain the MLP warnings.

Original local output versions and failure records remain preserved. This package provides the current derived reporting tables; the names above map to their exact source files in the manifest. A successful reproduction is a technical check, not independent scientific acceptance.

## Numerical reproduction

Run `python reproduce_pool.py` with Python 3. Only the standard library is required. The command verifies file hashes and recomputes all 24 field-equal means and descriptive 95% t intervals, all 192 leave-one-field-out estimates, positive field counts and the exact zero self-comparison. It also checks that all 10 MLP warning records are present.

To reproduce the executed SciPy 1.18.0 calculation at the retained absolute tolerance of `1e-10`, the stored critical value is `t(0.975, df=7) = 2.364624251592784`. These are exploratory intervals, with no confirmatory p-values or multiplicity-adjusted claims.

An optional receipt can be written to a new file:

```text
python reproduce_pool.py --output receipt.json
```

The receipt path must not already exist. The command does not reproduce training, raw prediction or family scoring, or check Git signatures and all original inputs. It verifies derived calculations rather than independently validating the scientific interpretation.

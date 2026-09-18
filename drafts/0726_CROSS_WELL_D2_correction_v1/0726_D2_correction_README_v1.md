# CROSS-WELL D2 corrected executor

This directory contains an outcome-independent implementation correction for
`CROSS_WELL_LAYER_D_RUN_001`.

The copied executor differs from the registered executor by exactly one frozen
conversion lookup entry:

```python
"x1_tonne_force_to_kkgf": 1.0
```

The semantic rule, unit mapping, cohort, models, baselines, scoring algorithm,
estimands, uncertainty plan and outputs are unchanged. The registered executor
and its failed partial output remain preserved separately.

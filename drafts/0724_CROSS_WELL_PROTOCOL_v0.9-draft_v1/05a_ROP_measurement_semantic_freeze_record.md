# ROP Measurement and Semantic Contract — Freeze Record

**Protocol component:** ROP Measurement and Semantic Contract  
**Status:** `PRINCIPALLY_FROZEN`  
**Effective date:** 2026-07-25  
**Outcome access at decision:** `NO_LAYER_D_OUTCOME_ACCESS`  
**Pending dependency:** `05b_measurement_alignment_sampling_contract.yaml`

## Frozen measurement construct

> Source-reported operational rate of penetration, harmonized to metres per
> hour, representing new-hole advancement during eligible active-drilling
> intervals.

The study does not assume that all providers use an identical ROP calculation
window or an identical internal generation algorithm. Irreducible differences
between sources shall be recorded as measurement heterogeneity and acquisition
lineage. They shall not be hidden through post hoc target recomputation,
target-distribution clipping, source-specific calibration, or outcome-informed
parameter tuning.

## Eligibility and transformation boundary

- Canonical unit: metres per hour.
- Permitted target transformation: deterministic unit conversion supported by
  source metadata.
- Prohibited target transformations: distribution matching, winsorization,
  clipping selected from Layer D outcomes, source-specific calibration, target
  imputation, smoothing introduced by the analysis team, and reconstruction
  chosen to improve prediction error.
- Eligible construct: new-hole advancement during active drilling.
- Zero, negative, non-finite, connection, off-bottom, and reaming observations
  are handled only by rules frozen before outcome unlock.
- No hard upper ROP truncation is permitted in the primary analysis. Finite
  positive extreme values remain scorable and are reported through diagnostics.
- Unknown provider aggregation windows or internal derivation algorithms are
  recorded as lineage heterogeneity rather than silently standardized.

## Non-relaxation rule

Unless a source-only audit demonstrates that a source cannot satisfy the frozen
unit, provenance, operational-state, or target-construct requirements, the ROP
semantic core shall not be modified because:

- the number of valid observations is reduced;
- a well, family, field, or source is excluded;
- data loss is high;
- cross-well model performance declines; or
- confirmatory results are unfavorable.

## Frozen governance sequence

1. Complete the Measurement Alignment and Sampling Contract.
2. Conduct a source-only audit without inspecting Layer D outcomes.
3. Freeze all transformation parameters and `parameter_register.csv`.
4. Apply an external trusted timestamp to the protocol, code, parameters, and
   immutable input inventory.
5. Unlock numeric outcomes only after the timestamp and freeze checklist pass.
6. Execute Layer D once through the frozen pipeline.

Source-only audit may occur before the external timestamp. It must not inspect,
summarize, or use confirmatory target values to select alignment tolerance,
maximum gap, resampling interval, duplicate rule, state-boundary buffer, or
other transformation parameters.

## Amendment rule

This semantic core stops changing when this record takes effect. A later
revision must be triggered by source-side semantic incompatibility and recorded
as a formal protocol amendment. A revision triggered by Layer D values or model
performance is not a confirmatory correction.


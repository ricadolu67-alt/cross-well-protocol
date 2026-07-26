# CROSS-WELL Outcome Custody Governance Decision

## Accepted mechanism

- Accepted by: Principal researcher
- Acceptance date: 2026-07-25
- Acceptance stage: pre-outcome, `v0.9-draft`
- Layer D ROP outcome access: `NO_LAYER_D_OUTCOME_ACCESS`

The principal researcher accepted the following custody mechanism:

> The principal researcher retains the original archives. Before T3, only
> frozen structural and label-blinded covariate-qualification procedures may
> operate on them; these procedures must not expose, retain, summarize or score
> numeric ROP. After all v1.0 freeze checks pass, OSF Registration and the
> GitHub signed immutable release are complete, the principal researcher alone
> may issue an explicit written single-use numeric-unlock instruction.

## Access boundary

Permitted before T3:

- archive identity, file inventory and SHA-256;
- headers, mnemonics, descriptions and units;
- prespecified MD, WOB, surface-RPM and standpipe-pressure QC summaries;
- qualification decisions produced by frozen rules;
- access logs and protocol-integrity evidence.

Prohibited before T3:

- numeric ROP values;
- ROP distributions or descriptive statistics;
- predictions, residuals or model-performance metrics;
- target-informed exclusions, transformations, thresholds or cohort changes;
- numeric outcome parser execution.

## Verification requirement

This governance decision does not by itself make freeze-check F16 pass. Before
v1.0 freeze, a fail-closed dry run must prove that:

1. an explicit request for ROP output fails;
2. a synthetic sentinel ROP value never appears in permitted output;
3. T1a emits no numeric arrays;
4. T1b emits only permitted covariate summaries;
5. every attempted access is logged;
6. the real Layer D numeric outcome parser remains uninvoked.

The resulting report and access log must be hashed into the freeze manifest.


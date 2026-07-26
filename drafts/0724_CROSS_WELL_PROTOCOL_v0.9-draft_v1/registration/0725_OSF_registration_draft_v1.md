# CROSS-WELL OSF Registration — Draft Form Text

> Status: `DRAFT_ONLY_NOT_SUBMITTED`  
> Intended evidence role: primary externally trusted timestamp  
> Submission condition: only after `v1.0_freeze_checklist.csv` is entirely PASS and
> Layer D ROP outcome remains inaccessible.

## Registrant metadata

- Name: Lu Yuhan（陆宇晗）
- Affiliation: Changzhou University
- Location: Changzhou, Jiangsu, China
- ORCID: https://orcid.org/0009-0006-8513-2732
- Roles: protocol owner, principal researcher and outcome custodian

## Proposed title

CROSS-WELL: A Confirmatory Protocol for Auditable Cross-Field Transport of
Depth-Indexed Conditional Rate-of-Penetration Models

## Research question

Does a source-only, frozen, non-causal conditional relationship
\(E[ROP\mid MD,WOB,RPM,SPP]\) retain baseline-relative predictive value across
prespecified external petroleum fields after row exposure, unresolved
dependence, measurement semantics, cohort construction, model choice and
analysis freedom are controlled?

## Scientific scope

The task is depth-indexed conditional ROP estimation using measured depth,
weight on bit, surface rotary speed and standpipe pressure. It is not
ahead-of-state forecasting. The fitted associations do not identify the causal
effect of manipulating WOB, RPM or standpipe pressure and must not be
interpreted as a drilling-control or optimization policy.

## Primary outcome and measurement construct

The target is source-reported operational rate of penetration, harmonized to
metres per hour, representing new-hole advancement during eligible
active-drilling intervals. Source-specific ROP calculation windows and
acquisition lineage will be recorded as measurement heterogeneity. Target
values will not be recomputed, distribution-matched, source-specifically
tuned, or clipped in response to confirmatory results.

## Cohort and stopping rule

All archives acquired by the prespecified acquisition cutoff and contained in
the immutable candidate inventory will be processed by the frozen
qualification rules. Outcome unlock will proceed only if the qualified cohort
meets the frozen minimum of eight independent fields from at least four basin
contexts and each primary field contains at least two scorable independent
families. Failing the threshold will not trigger outcome inspection or
result-dependent acquisition.

Exact cutoff, inventory hash, field/basin registry and qualification status
will be copied from the final `v1.0-frozen` package:

- acquisition cutoff: `TO_BE_COPIED_FROM_V1.0`
- candidate inventory SHA-256: `TO_BE_COPIED_FROM_V1.0`
- qualified field count: `TO_BE_COPIED_FROM_V1.0`
- basin-context count: `TO_BE_COPIED_FROM_V1.0`

## Label-blinded qualification

Before outcome unlock, target-domain covariates may be inspected only through
prespecified structural, semantic and quality-control procedures. They do not
enter model fitting, hyperparameter selection, representation selection,
normalization fitting or threshold calibration. ROP numeric values remain
inaccessible to the analysis team until the registration and freeze evidence
are complete.

## Models and comparators

- Primary learner: five frozen source-only ExtraTrees models with seeds
  20260722–20260726, fixed hyperparameters and NoGate. Family loss is computed
  separately for each seed and averaged equally.
- Primary comparator: SourceMedian, a constant derived only from the verified
  source ROP labels.
- Secondary comparator: frozen source-only Ridge using the same feature
  contract.

All model files, preprocessing values, training-row selection and source
manifests are identified by SHA-256 in the final freeze manifest.

## Primary loss and estimand

The primary family loss is MD-interval-weighted MAE. Native co-sampled shared-MD
records are used; the primary analysis performs no fuzzy cross-file join,
cross-stream time join, interpolation or pre-prediction resampling.

For family \(j\) in field \(f\), basin context \(b\):

\[
\Delta_{bfj}=MAE_{\mathrm{SourceMedian},bfj}
             -MAE_{\mathrm{FrozenExtraTrees},bfj}.
\]

Family effects are averaged within each field, and the primary estimand is the
equal-weight mean of eligible field effects. It is interpreted as mean
baseline-relative transport across the sampled petroleum fields represented in
the sampled basin contexts. No random-basin population inference is claimed.

## Primary uncertainty and robustness

The primary presentation consists of the complete field-effect table,
field-equal mean and small-sample t interval over fields. Prespecified
robustness analyses are leave-one-field-out, leave-one-basin-out and field
bootstrap. Basin-stratified bootstrap, wild-cluster methods and hierarchical
models are supplementary sensitivities and cannot replace the headline
analysis.

## Matched falsification diagnostics

Three diagnostics each have one frozen primary contrast and use the frozen
ExtraTrees learner:

1. split-induced optimism: the same test observations under clean family
   isolation versus prespecified within-family row exposure;
2. dependence-induced optimism: the same test observations under audited
   family exclusion versus nominal-file exclusion in identified dependence
   cases;
3. semantics-induced pessimism: target-side representation intervention under
   an otherwise frozen canonical pipeline.

F-15 is a retrospective semantic failure analysis and not an estimator of the
population-average semantic bias.

## Exclusions and attrition

Qualified and scorable families are distinct populations. A frozen field with
one scorable family remains in the cohort flow and family-level table but does
not enter the primary field-equal estimand. All exclusion and attrition reasons
are emitted by frozen rules; poor model performance is never an exclusion
reason.

## Deviations

A deviation may repair implementation or factual errors but may not change a
scientific decision rule in response to observed outcomes. Any post-unlock
scientific-rule change is a post hoc analysis or a new protocol version.
Outcome-independent technical corrections require retention of original
results and a full-cohort rerun.

## Registration attachments

The OSF registration will attach:

- the complete `CROSS_WELL_PROTOCOL_v1.0-frozen` archive;
- its SHA-256 digest;
- `16_freeze_manifest.json`;
- a human-readable SHA-256 inventory;
- freeze checklist and parameter register;
- an outcome-lock attestation signed by the authorized custodian;
- the Git commit/release identifiers when available.

The registration must be submitted before numeric ROP outcome unlock.

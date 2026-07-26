# CROSS-WELL Protocol v0.9-draft

## 1. Purpose

This directory is the pre-freeze engineering package for the CROSS-WELL study. It converts the agreed research design into parseable configuration files, tabular registries, output shells, validation rules, and a future hash manifest.

Version `v0.9-draft` is not a confirmatory freeze and must not be described as preregistered, externally timestamped, or outcome-locked. It may be promoted to `v1.0-frozen` only after every item in `v1.0_freeze_checklist.csv` is `PASS`.

Acquisition was explicitly closed by the principal researcher on
`2026-07-25T16:56:00+08:00`, before Layer D ROP outcome access. The immutable
v1.0 candidate inventory is integration v4: 102 files, 63,834,771,389 bytes,
with inventory SHA-256
`20917E0BFD144DC2D9EF10B3AA7C2EBA592A012C2CB7498720CF7CA6EBB0310B`.
This closure does not authorize outcome unlock.

The principal researcher also accepted the outcome-custody mechanism: original
archives remain under principal custody; only frozen fail-closed preunlock
commands may produce structural or covariate-QC evidence; numeric ROP access
requires a later explicit single-use instruction after all v1.0 checks, OSF
Registration and the GitHub signed immutable release are complete. Practical
access-control testing was completed using a synthetic sentinel archive:
explicit ROP output was rejected, permitted output contained no sentinel, and
no real Layer D archive was opened. Freeze-check F16 is `PASS`.

## 2. Scientific scope already fixed

- Task: depth-indexed conditional ROP estimation.
- Information set: MD, WOB, surface RPM, and standpipe pressure.
- Excluded claims: ahead-of-state forecasting, causal effects of manipulating drilling controls, closed-loop optimization, and deployment readiness.
- Primary learner: Frozen ExtraTrees.
- Primary comparator: SourceMedian.
- Secondary comparator: frozen source-only Ridge.
- Primary family loss: MD-interval-weighted MAE.
- Primary independent unit: petroleum field.
- Primary estimand: field-equal mean absolute Transfer Gain.
- Basin role: sampled replication context, not a random-basin population estimand.
- Confirmation: Layer B, C, and D remain separate.
- F-15 role: retrospective semantic failure analysis, not a confirmatory average semantic-bias estimator.

## 3. Draft placeholders

Every unresolved value is represented by the exact token `TO_BE_FROZEN` or a string beginning with it. A draft may validate structurally while still failing freeze readiness. The validation script reports both conditions separately.

Do not replace a placeholder using Layer D ROP values or model-performance feedback. Governance values must be justified by study governance; sampling and loss parameters may be justified only by source-side geometry, metadata, or engineering representation; execution values must be fixed from the reproducible environment.

## 4. Directory map

The numbered files are the 16 protocol modules:

1. `01_deployment_claim.yaml`
2. `02_candidate_acquisition_plan.yaml`
3. `03_unit_registry.csv`
4. `04_dependence_rules.yaml`
5. `05_measurement_semantic_contract.csv`
6. `06_label_blinded_qualification.yaml`
7. `07_falsification_diagnostics.yaml`
8. `08_model_baseline_manifest.json`
9. `09_loss_and_estimands.yaml`
10. `10_uncertainty_plan.yaml`
11. `11_confirmatory_cohort_manifest.csv`
12. `12_outcome_lock_and_custody.yaml`
13. `13_output_table_shells/`
14. `14_claim_wording_matrix.md`
15. `15_protocol_deviation_log.csv`
16. `16_freeze_manifest.json`

Additional control files:

- `parameter_register.csv`: value, category, basis, provenance, decision date, and outcome-access status for each parameter.
- `v1.0_freeze_checklist.csv`: hard PASS/FAIL release gate.
- `registration/0725_acquisition_closure_record_v1.md`: principal-researcher
  closure decision and immutable 102-file inventory identity.
- `registration/0725_outcome_custody_decision_v1.md`: accepted preunlock access
  boundary, sole unlock authority and mandatory fail-closed test.
- `registration/0725_outcome_lock_access_test_v1/`: synthetic sentinel fixture,
  access log, machine-readable result, report and evidence manifest.
- `scripts/test_outcome_lock_synthetic.py`: synthetic-only fail-closed access
  test; its path guard does not accept a real Layer D archive.
- `registration/0725_measurement_semantic_contract_audit_v1/`: metadata-only
  completeness audit proving that all 23 qualified archive scopes contain the
  exact common4-plus-ROP contract without numeric ROP access.
- `scripts/audit_measurement_semantic_contract.py`: deterministic semantic
  completeness validator used for freeze-check F07.
- `registration/0725_synthetic_full_dry_run_v1/`: full synthetic pipeline
  result, report, manifest and all ten populated output shells.
- `scripts/run_synthetic_full_dry_run.py`: deterministic dry-run implementation
  of MD-weighted loss, scorable attrition, field aggregation, uncertainty,
  diagnostic-output routing, claim routing and execution tracing.
- `14a_claim_wording_rules.csv`: machine-readable companion to the manuscript
  claim wording matrix.
- `15a_protocol_deviation_rules.json`: executable D1/D2/D3 pre- and post-unlock
  disposition rules.
- `registration/0725_claim_deviation_rule_test_v1/`: passing machine test of
  all claim and deviation governance branches.
- `registration/0725_principal_dependence_cohort_review_v1/`: validated
  36-family and 13-field label-blinded review packet awaiting principal
  acceptance before F06/F15 can pass.
- `scripts/build_principal_dependence_cohort_review.py`: deterministic builder
  for the principal dependence and final preunlock cohort review packet.
- `03e_final_preunlock_dependence_registry.csv`: principal-approved final
  36-family dependence registry.
- `11e_final_preunlock_cohort_manifest.csv`: principal-approved final preunlock
  family manifest retaining 23 qualified and 13 held families.
- `11f_final_preunlock_field_manifest.csv`: final 13-field manifest, including
  8 primary-qualified fields across 5 basin contexts.
- `scripts/finalize_principal_dependence_cohort.py`: deterministic finalizer
  used after principal acceptance; it reads no numeric ROP.
- `03a_preunlock_extension_unit_registry.csv`: official identity and conservative dependence rows for the five-file 2026-07-25 extension.
- `11a_preunlock_extension_cohort_manifest.csv`: T1a/T1b and attrition status for the same extension.
- `03b_preunlock_extension_v2_unit_registry.csv`: Blacktip P1/P2 archive-to-family registry for extension v2.
- `11b_preunlock_extension_v2_cohort_manifest.csv`: extension-v2 T1a/T1b negative-result and attrition record.
- `03c_preunlock_extension_v3_unit_registry.csv`: Scarborough 5 and conservative Scarborough 4/4A archive-to-family registry.
- `11c_preunlock_extension_v3_cohort_manifest.csv`: extension-v3 T1a/T1b negative-result and attrition record.
- `03d_preunlock_extension_v4_unit_registry.csv`: Prelude P3/P4/P6 official identity and family registry.
- `11d_preunlock_extension_v4_cohort_manifest.csv`: extension-v4 qualified-family and primary-field record.
- `05c_label_blinded_semantic_mapping_amendment_v1.yaml`: global preunlock
  exact-token amendment for `TOTDEPTH` and WOB units `klbs`/`t`.
- `05d_extension_v4_measurement_semantic_contract.csv`: 15 archive-specific
  feature-target semantic rows for the three qualified Prelude families.
- `05a_ROP_measurement_semantic_freeze_record.md`: principally frozen ROP
  construct, transformation boundary, and amendment rule.
- `05b_measurement_alignment_sampling_contract.yaml`: deterministic native-row
  alignment, segment, duplicate, weighting, coverage, and block rules.
- `source_only_audit/`: aggregate Volve/source sampling audit and parameter
  evidence; it contains no Layer D outcome.
- `schemas/SCHEMA.md`: field definitions and controlled vocabularies.
- `scripts/validate_protocol.py`: syntax, columns, cross-file values, placeholders, and manifest-coverage checks.
- `scripts/generate_freeze_manifest.py`: v1.0 前生成文件哈希和
  `SHA256SUMS.txt`；默认拒绝任何非 PASS 检查项或未冻结占位符。
- `registration/`: OSF Registration、GitHub signed release 与 Zenodo 最终 DOI
  的草拟文本、证据计划和上传清单；当前均未提交。

## 5. Protocol lifecycle

```text
v0.9-draft
  -> source-only or synthetic dry run
  -> all freeze checks PASS
  -> v1.0-frozen
  -> trusted timestamp while outcome remains inaccessible
  -> outcome unlock
  -> single frozen execution
  -> immutable raw results and claim-boundary report
```

Pre-unlock corrections require a new complete manifest, new hashes, a new timestamp, and an explicit supersession note. Post-unlock scientific-rule changes are post hoc analyses or a new protocol version, not corrections to the confirmatory analysis.

## 6. Validation

From this directory, run:

```powershell
python scripts/validate_protocol.py .
```

Exit meanings:

- `0`: structurally valid; the report still states whether freeze readiness passed.
- `1`: parse, schema, cross-file, or manifest-coverage error.

Before `v1.0-frozen`, run again with:

```powershell
python scripts/validate_protocol.py . --freeze-ready
```

This stricter mode fails if any `TO_BE_FROZEN` token remains, any checklist item is not `PASS`, or a manifest hash is not a lowercase SHA-256 digest.

## 7. Dry-run acceptance

The source-only or synthetic dry run must automatically generate every table in `13_output_table_shells`, including cohort flow, family metrics, field effects, leave-one-field-out, leave-one-basin-out, diagnostic contrasts, and claim output. If the executor must decide how to handle an individual well, gap, unit, ambiguity, or attrition case during execution, the protocol is not ready to freeze.

## 8. Non-negotiable meta-rule

> No scientific rule may be relaxed, extended, or replaced on the basis of observed Layer D outcomes. Any post-unlock scientific-rule change constitutes a post hoc analysis or a new protocol version, not a correction to the confirmatory analysis.

## 9. Current pre-freeze cohort status

The active cohort combines T1b v4 with the prespecified five-archive
pre-unlock extension acquired on 2026-07-25. Both stages select one canonical
source object per family using the same frozen covariate-QC and coverage rules,
without converting, retaining, summarizing, or scoring ROP.

- 102 immutable acquisition files in the current preunlock snapshot;
- 36 development families assessed;
- 23 label-blinded qualified families;
- 13 petroleum fields represented;
- 8 fields have at least two qualified families;
- those primary-qualified fields span 5 normalized basin contexts.

Montara became primary eligible after two extension-v1 families passed.
Macedon remained in the attrition flow because both candidates failed frozen
surface-RPM completeness. Extension v2 then assessed Blacktip P1 and a new P2
archive. Both supplied CRPM/TRPM but no curve defensibly identified as surface
RPM, so they were held without semantic remapping. The field minimum remains
8. Extension v3 then assessed Scarborough 5 and the conservative Scarborough
4/4A family. Their LWD and PWD objects did not place MD, WOB, surface RPM, SPP
and a unique ROP header in one frozen source object; cross-file numerical
alignment was not introduced post hoc. The outcome-unlock gate therefore
remains `FAIL_7_OF_8` and ROP remains locked.

Extension v4 assessed Prelude P3, P4 and P6. The initial fail-closed pass retained
all three as held because `Tot Depth` and WOB units `klbs`/`t` were absent from
the restricted mapping table. A formal global preunlock amendment added only
these exact engineering synonyms. A fixed scan of 30 prior T1b QC files found
zero affected prior objects, so no previous family decision changed. All three
Prelude families then passed the unchanged covariate and coverage thresholds,
making Prelude the eighth primary-qualified field. The minimum field/basin gate
is now `PASS_8_OF_8` and `PASS_5_OF_4`; ROP nevertheless remains locked until
final inventory closure and every v1.0 freeze requirement is complete.

## 10. Accepted dependence/cohort and validated diagnostics

The principal researcher accepted the complete dependence/cohort review
packet. The final preunlock registry contains 36 unique conservative families;
the final cohort manifest retains 23 qualified and 13 held families. Thirteen
fields are represented, of which 8 are primary-qualified across 5 basin
contexts.

The source-only falsification configuration passed complete execution. Five
fixed 100 m test intervals were used for the mechanism-isolated split contrast
with `q = 0.05`, 16,000 matched training rows, 800 replacement rows and the
five frozen model seeds. The two identified dependence cases were run under
both operational and matched-training-size conditions. F-15 remains a
retrospective semantic failure analysis and is not a confirmatory average-bias
estimator. No Layer D archive was opened.

Every uncertainty-analysis branch passed synthetic validation: the complete
field table, equal-field mean, small-sample t interval, ordinary and
basin-stratified field bootstraps, Rademacher wild-cluster bootstrap-t, and the
self-contained Gaussian basin-random-intercept REML sensitivity. Supplementary
methods cannot replace the headline field table or t interval.

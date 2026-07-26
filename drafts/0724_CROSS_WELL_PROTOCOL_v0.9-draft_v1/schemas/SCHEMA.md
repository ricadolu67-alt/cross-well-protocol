# Schema and controlled vocabularies

## Global conventions

- Encoding: UTF-8.
- Dates and times: ISO 8601; operational timestamps use UTC and end in `Z`.
- Hashes: lowercase SHA-256, exactly 64 hexadecimal characters.
- Missing draft values: a dedicated unresolved-value token; none is permitted in a payload-ready package.
- Boolean values in YAML/JSON: native `true` or `false`.
- Boolean values in CSV: lowercase `true` or `false`.
- IDs: stable strings; never derive independence from filenames alone.
- Canonical ROP unit: to be recorded in the completed measurement-semantic contract.
- Canonical MD unit: metre unless a later pre-outcome contract version explicitly documents another canonical unit.

## Controlled statuses

### `record_status`

- `TEMPLATE`: required contract row awaiting archive-specific completion.
- `EXAMPLE`: illustrative row that must be removed before freeze.
- `ACTIVE`: real protocol record.
- `PRINCIPALLY_FROZEN`: semantic core fixed before all dependent numeric
  alignment/sampling parameters and archive-specific mappings are complete.

### Qualification statuses

- `PENDING`
- `PASS`
- `FAIL`
- `EXCLUDE`
- `NOT_APPLICABLE`

### Semantic ambiguity

- `PASS`: one supported canonical mapping.
- `EXCLUDE`: ambiguity cannot be resolved without outcome feedback.
- `SENSITIVITY`: multiple plausible mappings were specified before outcomes.
- `EXTERNAL_GATE_PENDING`: post-payload evidence required before unlock, not a missing payload parameter.

`PRINCIPALLY_FROZEN` is permitted only for a semantic core whose remaining
dependencies are explicitly named. It is not equivalent to `v1.0-frozen`.

### Freeze checklist

- `PENDING`
- `PASS`
- `FAIL`

Only `PASS` is acceptable at v1.0 freeze.

### Protocol deviations

- `D1`: administrative; no analysis effect.
- `D2`: outcome-independent technical or factual correction; retain original results and rerun the full cohort after unlock.
- `D3`: scientific-rule change; after unlock it is post hoc or belongs to a new protocol version.

## `03_unit_registry.csv`

- `archive_id`: stable archive identifier.
- `archive_sha256`: hash of the immutable raw archive.
- `basin_id`, `field_id`, `well_id`, `wellbore_id`, `branch_id`: explicit hierarchy identifiers.
- `dependence_family_id`: primary conservative independent-family identifier.
- `identity_evidence`, `dependence_evidence`: traceable source or evidence reference.
- `qualification_status`: current structural/cohort status.
- `exclusion_reason_code`: one of the codes in module 02.

## `05_measurement_semantic_contract.csv`

Each raw mnemonic and archive scope receives its own row. Features and the ROP target are governed together.

- `variable_role`: `feature` or `target`.
- `canonical_name`: canonical variable name.
- `physical_definition`: physical measurement, not merely a mnemonic expansion.
- `measurement_location`: surface, downhole, wellbore, derived, or explicitly documented alternative.
- `sampling_basis`: depth-indexed, time-indexed, or derived.
- `aggregation_window`: documented window or `unknown`.
- `operational_state`: drilling-state eligibility.
- `conversion`: deterministic formula to canonical units.
- `physical_range_rule`: frozen numeric rule and unit.
- `smoothing_status`, `derived_status`: whether the published series was transformed.
- `evidence_source`: WITSML, data dictionary, provider report, or traceable documentation.
- `ambiguity_status`: controlled value listed above.
- ROP-specific columns define instantaneous/average status, time/depth derivation, exclusion rules, and zero/negative/upper-range policy.

Prediction error must never be used to select a semantic mapping.

## `11_confirmatory_cohort_manifest.csv`

- T1a and T1b statuses record structural and label-blinded covariate qualification.
- `T2_qualified` identifies the frozen qualified population.
- `scorable_status_T3` is determined only after outcome unlock using frozen scoring-coverage rules.
- A field enters the primary estimand only if `primary_field_eligible` is true and it has at least two scorable independent families.
- Qualified but unscorable families remain in the flow and are never silently deleted.

## `parameter_register.csv`

Categories:

- `A`: governance and scientific-decision parameters, independent of performance.
- `B`: parameters justified by source-only geometry, metadata, or engineering representation.
- `C`: deterministic execution and software-environment parameters.

`outcome_access` must remain `NO_LAYER_D_OUTCOME_ACCESS` until the authorized unlock.

## Output shells

The shells are immutable column contracts. A dry run or frozen execution may add rows but may not delete or rename columns. If an analysis is unavailable, emit the header and a documented status row rather than omitting the file.

## Manifest rules

`16_freeze_manifest.json` must cover every protocol-control file plus external model, code, parser, and environment artifacts. The manifest file itself is not self-hashed. At freeze:

1. remove example rows;
2. fill all placeholders;
3. calculate file hashes;
4. validate;
5. sign;
6. obtain the external trusted timestamp while outcome access remains closed.

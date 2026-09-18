# Publication note for the D2-corrected executor

Published: 2026-09-19. Correction made and executed: 2026-07-26.

## What this folder is

`run_layer_d_confirmatory.py` in this folder is the executor that produced the
reported Layer D results (`CROSS_WELL_LAYER_D_RUN_001`, corrected full-cohort
rerun). It differs from the registered executor in the frozen release
`cross-well-protocol-v1.0` by exactly one line in the frozen unit-conversion
lookup:

```python
"x1_tonne_force_to_kkgf": 1.0,
```

The first authorized execution stopped because the registered executor lacked
this entry for a unit token (`t`, tonne-force) that the frozen scoring source
map already specified. The factor 1.0 is fixed by that frozen map. No cohort,
feature, model, baseline, scoring rule, estimand or uncertainty rule changed.
The manuscript discloses this correction and the fact that it was made after
family-level outputs from the stopped attempt were visible.

## Why it is published now

Until 2026-09-19 this folder was retained locally but was not in the public
repository, so the public code could not re-execute the full Layer D chain.
It is published so that others can reproduce the reported run end to end.
The git commit date is therefore the publication date, not the correction date.

## Integrity

The files are byte-identical to those recorded on 2026-07-26 in
`0726_D2_correction_manifest_v1.json`:

| File | SHA-256 |
|---|---|
| `run_layer_d_confirmatory.py` | `970141BAFAD66A2C49A40222200D1862B4A97A41E4E7187235D7D467F6D14E17` |
| `test_uncertainty_plan.py` | `A814D3DC7818DC9C5286318B1B29D4945723B855DF4A8E02DE0E4EE71CADEBFA` |
| `0726_D2_correction_README_v1.md` | `59191DE378992C688AA932374C95D369895842212FB80593AD3984818C809EC4` |

The registered executor remains unchanged at
`drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1/scripts/run_layer_d_confirmatory.py`
(SHA-256 `DE5CF8AEE34C113DD309FFD3EC01626A61B79EC61D7AF225C9E864C2E42D12A6`).
The failed partial output of the first attempt is retained privately because it
contains row-level values derived from NOPIMS archives, which this repository
does not redistribute.

## How to use it

Run this executor with `--protocol-root` pointing to
`drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1`. The executor still enforces the
frozen external unlock gate and the private archive locator; upstream NOPIMS
archives must be obtained from NOPIMS and verified against the SHA-256 values in
`registration/0726_frozen_scoring_source_map_v1.csv`.

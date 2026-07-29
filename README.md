# XW-AUDIT protocol and headline reproduction

This repository preserves the auditable protocol and executable artifacts for:

> **XW-AUDIT (Cross-Well Audit of Deployment, Units, Independence and Transport): quantifying evidence distortion and confirming baseline-relative cross-field transport of a frozen conditional ROP model**

XW-AUDIT treats a cross-well generalization claim as an evidence experiment. It fixes a depth-indexed, non-causal rate-of-penetration (ROP) claim; audits provenance, dependence and predictor-target measurement semantics; quantifies matched evidence distortions; freezes analytical freedom; and aggregates external evidence at the independent field level.

XW-AUDIT was registered under the working name **CROSS-WELL**. The immutable release tag, frozen filenames, run identifiers and historical paths retain that registered working name; this is a nomenclature change only and does not alter the protocol, cohort, models, endpoints, estimands or confirmatory procedures.

## Evidence status

- The immutable pre-outcome protocol is preserved in release [`cross-well-protocol-v1.0`](https://github.com/ricadolu67-alt/cross-well-protocol/releases/tag/cross-well-protocol-v1.0).
- That release remains anchored to verified signed commit `50e964a67bf24f4f4bea890d34eac77cde53e476`.
- The OSF registration is embargoed through 31 December 2028. A confidential view-only reviewer link is provided only through the journal's private submission or editorial channel and is intentionally not stored in this public repository.
- The post-unlock reproduction files in `reproduction/` are derived from the retained field-level outputs. They do not alter the frozen release.

## Reproduce the headline result

Windows (Command Prompt or double-click):

```bat
reproduce_headline.cmd
```

PowerShell users may alternatively run `powershell -ExecutionPolicy Bypass -File .\reproduce_headline.ps1`.

macOS/Linux/Git Bash:

```bash
bash reproduce_headline.sh
```

The command uses only the Python standard library. It verifies the derived input hash, recomputes the eight-field equal mean Transfer Gain and small-sample interval, recomputes the family-then-field equal log MAE ratio, checks the Gorgon `3`-family count, and writes:

- `reproduction/generated/headline_summary.json`
- `reproduction/generated/headline_field_effects.svg`

Expected headline values:

- field-equal Transfer Gain: `+2.071869 m/h`
- 95% small-sample t interval: `+1.024861 to +3.118876 m/h`
- family-then-field equal log MAE ratio: `-0.093070`
- primary fields: `8`; all field gains positive

## Repository map

- `drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1/` — protocol modules and executable pipeline preserved for the frozen release
- `reproduction/` — small, post-unlock, derived-data headline reproduction
- `content/0730_XW_AUDIT_v17.8.6_pre-submission/integrity_companion/` — byte-identical copies and a SHA-256 crosswalk for four historical evidence records listed by, but absent from, the earlier integrity-package directory
- `LICENSE` — license for original author-created code and documentation

## Data and license boundary

Original author-created code and documentation are released under the MIT License. NOPIMS archives and other upstream datasets are **not** relicensed or redistributed here; they remain subject to provider terms. Package identifiers, member paths and cryptographic hashes are recorded in the protocol artifacts so eligible users can reconstruct provenance without this repository republishing upstream data.

## Claim boundary

The frozen result supports baseline-relative conditional transport among sampled, data-qualified petroleum fields. It does not establish future forecasting, causal drilling optimization, deployment readiness, universal nonlinear-model superiority, engineering adequacy or inference to a probability-sampled basin population.

# CROSS-WELL Layer D Acquisition Closure Record

## Governance decision

- Protocol stage: `v0.9-draft`, pre-outcome
- Decision authority: Principal researcher
- Confirmation received: `2026-07-25T16:56:00+08:00`
- Equivalent UTC time: `2026-07-25T08:56:00Z`
- Layer D ROP outcome access at confirmation: `NO_LAYER_D_OUTCOME_ACCESS`
- Model execution at confirmation: `NOT_RUN`

The principal researcher explicitly confirmed closure of acquisition and
accepted the integration-v4 102-file inventory as the final candidate
inventory for the planned v1.0 confirmatory protocol.

## Frozen inventory identity

- Inventory:
  `../0725_CROSS_WELL_preunlock_integration_v4/0725_combined_acquisition_inventory_v5.csv`
- File count: `102`
- Total bytes: `63834771389`
- Inventory SHA-256:
  `20917E0BFD144DC2D9EF10B3AA7C2EBA592A012C2CB7498720CF7CA6EBB0310B`
- Development families: `36`
- Label-blinded qualified families: `23`
- Petroleum fields: `13`
- Primary-qualified fields: `8`
- Represented primary basin contexts: `5`

## Consequences

1. No archive acquired after this confirmation may enter the current
   confirmatory cohort.
2. Earlier extension windows nominally ending on 2026-07-27 are superseded by
   this explicit early-closure decision.
3. Newly discovered or subsequently acquired data require a separately
   versioned acquisition phase and cannot be appended after outcome unlock.
4. The ROP outcome remains locked until every remaining v1.0 freeze-checklist
   item is `PASS`, the final manifest is generated, and the external timestamp
   evidence is obtained.
5. This closure does not itself authorize numeric outcome unlock.


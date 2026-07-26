# Principal Dependence and Cohort Review Packet

- Generated: `2026-07-25T10:00:55.461909+00:00`
- Source: integration-v4 label-blinded metadata only
- Numeric ROP accessed: `false`
- Development families: `36`
- Qualified families: `23`
- Petroleum fields: `13`
- Proposed primary fields: `8`
- Represented primary basin contexts: `5`
- Duplicate proposed family IDs: `0`
- Packet validation: `PASS`

## Proposed rule

Each traceable NOPTA well ID is one conservative dependence family.
A sidetrack or branch named inside that well record remains inside the
same family. No separate qualified rows share a NOPTA ID, and no
cross-row merge is proposed. Held families remain visible in the flow.

## Required principal action

Review the two CSV files and either accept the complete proposed
registry or identify exact rows requiring correction. Acceptance will
close F06 and permit generation of the final preunlock cohort manifest
for F15. It does not authorize numeric outcome access.

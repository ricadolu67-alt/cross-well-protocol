# CROSS-WELL Outcome-Lock Synthetic Access Test

- Executed: `2026-07-25T09:05:30.747198+00:00`
- Scope: `SYNTHETIC_FIXTURE_ONLY`
- Real Layer D archives opened: `false`
- T1a numeric arrays emitted: `false`
- T1b target tokens converted: `0`
- T1b target summaries emitted: `0`
- Prohibited ROP request exit code: `17`
- Sentinel found in permitted outputs: `false`
- Overall status: `PASS`

The synthetic fixture contains a target sentinel, but the permitted
preunlock outputs contain no sentinel value. The explicit target-output
probe failed closed. No real Layer D archive was opened by this test.

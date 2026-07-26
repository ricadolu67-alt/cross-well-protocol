# Output table shells

These CSV files define mandatory outputs for the dry run and frozen execution. Headers must not be deleted or renamed after freeze. Empty tables must still be emitted with headers so that null or failed analyses remain visible.

Required flow:

1. `01_candidate_flow.csv`
2. `02_family_metrics.csv`
3. `03_field_effects.csv`
4. `04_basin_context_summary.csv`
5. `05_leave_one_field_out.csv`
6. `06_leave_one_basin_out.csv`
7. `07_falsification_diagnostics.csv`
8. `08_uncertainty_summary.csv`
9. `09_claim_boundary_output.csv`
10. `10_execution_trace.csv`


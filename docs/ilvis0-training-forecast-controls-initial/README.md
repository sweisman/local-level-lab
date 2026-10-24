# Initial training/forecast worker check

The initial frozen run charged all 24 generated-control identities, but none
reached initialization or fitting. The shared worker loads its adapter as a
standalone module; relative imports in the adapter therefore failed.

No native calculations or aircraft observations were used. The failures and
charged identities are preserved. This completed study will not restart.
A separate loader regression test reproduces the fault; a corrected adapter
requires a new freeze with unchanged scientific controls and limits.

[Current prediction protocol](../PREDICTION_VALIDATION.md)

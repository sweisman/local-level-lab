# Declare training error allowances explicitly

The short-example rebuild uses a fixed 1 mm observation allowance. A longer
study needs to state its own assumptions, rather than inherit that number.
Keep the completed short-example implementation and all its freezes unchanged.

Add a separate necessary-constraint builder requiring a finite, nonnegative
allowance for every training epoch and coordinate. No scalar broadcasting,
default noise level, future observation or automatic instrument specification
is permitted. Preserve all 27 physical columns, all 24 shared expression columns
and the existing 27 product coordinates, including unidentifiable directions.
Retain the separate saved arithmetic allowance and outward rounding.

Focused deterministic tests check every row against independently assembled
rational arithmetic, agreement with the old builder when explicitly supplied
1 mm, changed per-axis allowances, nonzero centers and invalid inputs. These
are small one-thread tests, reserving one thread for the active growth screen.
No native integration, optimizer or aircraft observation is used.

This interface checks row construction from supplied bound reports. Its caller
must independently establish source bindings, complete domain coverage and the
justification of the allowances. Passing does not establish an error law,
calibrated coverage or useful complete-record predictions.

[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Recording-length requirements](../ilvis0-three-source-complete/NEXT_PLAN.md).

# Find the forecast-conditioned margin with a compact state

The [first search](ESA_CALIBRATION_CONDITIONED_MARGIN_RESULT.md) stopped
at the iteration limit. This experiment uses the same equations with
one extra variable per forecast state at the chronological cut. The
first group of equations maps the earlier error to that state. The
second propagates the state to the later error. This avoids the dense
matrix connecting every earlier coordinate to every later coordinate.

Use the same 400 earlier and 120 later epochs, 102 calibration columns,
parameter boxes, nine later drift terms, receiver covariance and
nominal forecast pair. Freeze the earlier result and reuse its certified
bracket. A single interior-point proposal receives at most 2,000
iterations and 30 seconds. Verify any improvement with the existing
exact drift cancellation and outward-rounded forecast and adjoint.
Retain the previous bracket if either side fails to improve. Compare
the outcome with the existing 4.03 cm integration-error target. No
aircraft fit, uncertainty calibration or scientific decision is made.

The study has one task, one numerical thread, five bound calls, 2,004
charged steps and a 180-second cooperative wall allowance. The same
verified recovery policy allows one separately charged interrupted-task
attempt. There are zero native calls and zero reads of reserved flights.

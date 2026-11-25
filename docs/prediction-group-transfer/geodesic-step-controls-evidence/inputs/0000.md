# Test a direction correction after a rejected full step

Reuse the eight original generated starts with known optima, including
interior, upper-bound, lower-bound and weak-direction fits. Keep their
physical boxes, acceptance ratio, full fresh stopping check, known-answer
tolerances and 40-evaluation cap. Keep the old current-solver and
shorter-step outcomes as sealed controls.

When a full bounded step is rejected, subtract its linear residual
prediction from its evaluated residual. Use this difference as an
estimate of the quadratic bend along the step. For a candidate fraction
of the step, cancel the predicted bend in derivative directions with
singular values at least 0.001 times the largest. Apply just enough of
the correction to stay within the original calibration box. Retain all
directions in the original solve and final stopping check.

Consider fractions 1, 1/2, 1/4 and 1/8 in that order. Evaluate once at
the feasible corrected point with the largest positive predicted
decrease. Accept it only if its actual decrease is positive and at
least one tenth of the prediction. The unchanged trust-region fallback
handles a failed or unavailable correction. This option must pass all
eight known-answer cases before a separate generated flight-scale test.

Freeze eight tasks on one numerical thread and allow at most 320
charged residual/tangent evaluations in 60 seconds. Use the existing
qualified task recovery. The inputs are generated controls. No aircraft
measurements, original native fits or reserved flights enter the test.
[Earlier shorter-step test](CURVATURE_RETRY_CONTROLS_RESULT.md)

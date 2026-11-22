# Trace GPS carrier-phase error into the saved shape score

Use the sealed satellite-influence study on ESA development flight 187 and
its same 1,038 steps, earlier anchor and 400/120 shape-score operator. Recover
each ECEF least-squares gain from the saved omission correction and withheld
range residual. Require every denominator to be finite and nonzero. Validate
the accumulated gain against all 12 published single-satellite score changes
within 0.00002 score units. The remaining difference allows for linearizing
the conversion from Earth-centered positions to the scoring coordinates.

Compute the derivative of the saved shape score with respect to each
ionosphere-free range observation. Include both endpoints of each step with
opposite signs, and keep every recorded satellite support change. Report
score sensitivity under four explicit error patterns.

1. Independent endpoint noise of equal variance. Compare with independent
   step errors at the same marginal variance for each phase difference.
2. An arbitrary bounded range error at each satellite and endpoint.
3. A constant offset for each satellite, and an offset shared by all
   satellites at each endpoint, as cancellation checks.
4. A linear phase drift for each satellite, expressed per minute.

Report the error scale associated with one score standard deviation reaching
the tie margin for case 1, and the smallest linearized worst-case scale
that could reach a tie for cases 2 and 4. These are sensitivities for the
frozen paths. There is no assumed error distribution for the real recording.
Separate closure of the exact nonlinear calibration region and observed
error-law qualification are still required.

One task on one numerical thread has a 45-second cooperative limit, one
adjoint pass, 1,038 charged step evaluations and up to 32 satellite rows per
step. Use only archived artifacts and the linearized score. There are no
new navigation solutions, inertial fits, forecasts or reserved-flight reads.

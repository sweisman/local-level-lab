# Integration interval and calibration geometry controls

Question: do the short geographic controls' Z gyro-offset errors come from finite
integration intervals amplified by weak calibration geometry?

Keep the known 12-second equatorial trajectory, 24 receiver epochs, latency, initial
state and interior calibration identical to the completed geographic controls.
Keep both angular-rate and specific-force integration independent of the native
predictor. Preserve the original generator and all its evidence.

Reintegrate the continuous analytic motion at 2.5 ms and 1.25 ms, instead of the
original 5 ms. Generate fresh integrals; do not split or interpolate measured data.
The finer streams are synthetic 400/800 Hz controls, not new NASA observations.
Test all three true models, using the original shape solver from zero with the same
six parameters, physical box and synthetic receiver covariance.

Add one roll-excited control for each model at 1.25 ms: body roll is
0.35 sin(2πt/5.1) radians. Pitch/yaw, receiver trajectory and injected calibration
remain the same. This is a deliberately informative software motion, not a claim
that the NASA recordings contain this attitude pattern.

There are nine new fit identities, no retries, at most 200 native sweeps per identity
including the two final value predictions: a maximum 1,800 fit sweeps. Reuse the three
saved original-solver/zero-start/interior 5 ms results; never refit them. Before each
fit, one extra truth tangent checks the independent track and records conditioning.
Thus the report allows at most 1,809 sweeps, with at most two numerical threads.
Ordinary focused unit tests have separate small software calls. Zero observed starts.

Each fit uses the original control's convergence/prediction/objective checks, with
the nonzero continuous-to-midpoint reference error retained. Report offset error,
gain error, active limits, singular values, condition, objective and prediction error
whether or not the fit passes. Do not demand an exact second-order ratio: covariance,
off-packet evaluation, floating-point effects and weak directions can change it.

Success means explaining an observed error trend or rejecting the proposed mechanism,
not choosing an Earth model. Reduction with interval size tests integration error;
the matched fine-interval roll control tests geometry separately. Neither alone
identifies the NASA boundary mechanism, instrument preprocessing or true sampling
period. No observed profiles or corpus reruns are authorized.

Hash this plan, source/configuration, native builds, environment and reused artifacts
before the first fit. Charge starts durably; an interrupted start remains a failure
without retry. Preserve outputs and completed journals. Packaging must use saved
results without invoking an optimizer.

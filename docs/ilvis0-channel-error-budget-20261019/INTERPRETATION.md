# What the error-budget controls revealed

The batch completed **46 diagnostic identities** in 2.11 seconds, with all
implementation checks passing. Of 108 candidate/trajectory combinations, 81
pass both declared approximation screens. The other 27 remain visible; no
smoothing window or physical model was selected from these outcomes.

These counts describe deterministic software controls, not observed flights,
statistical coverage or instrument performance. The same constructed trajectory
is checked under several hypotheses; those are not independent observations.

## Longer windows reduce noise but can miss motion

For the lower assumed receiver-noise level, a quadratic fit with a 16-second
half-window produces as much as **0.0124 m/s²** of force-magnitude bias. Its
declared linear standard deviation is about 0.00263 m/s², so the truncation
screen fails. At an eight-second half-window the bias is about 0.00326 m/s²,
also above the declared relative limit.

A quartic fit follows this constructed motion more closely. At the 16-second
half-window its maximum bias is about 0.00077 m/s² with a declared standard
deviation near 0.00696 m/s². Its screen passes here. That is not a general
recommendation for real recordings: different maneuvers and receiver errors can
change the trade-off.

The high-noise, short-window quartic controls fail the local nonlinear screen.
Conversely, increasing assumed noise can make a truncation-to-noise ratio pass
while making the diagnostic much less informative. **Passing an approximation
screen is not evidence that a recording can distinguish models.**

## Acceleration aggregation changes the observable

In the exact one-second, 200 Hz rotation control, summing body-frame vectors
before taking their magnitude loses about **0.00311 m/s² at a 5° turn** and
**0.0497 m/s² at a 20° turn**. Averaging individual packet magnitudes has much
smaller finite-packet losses in this construction.

Those angles are mathematical controls, not measurements of the selected flight
stretches. The result shows why the chosen aggregation must be specified. An
archival permanent mount does not make force direction constant in the aircraft's
axes. Small rapid motion and finite packet integration still need treatment.

## Magnitude noise has a mean shift

Under the assumed isotropic acceleration-noise model, taking a norm raises its
mean. For the constructed 9.81 m/s² force and σ = 0.1 m/s², the shift is about
**0.00102 m/s²**. Independent quadrature orders agree with the small-noise
prediction in all four tested cases. Averaging more magnitudes does not remove
that mean shift.

These noise values are not estimates of any Applanix unit. Actual noise,
quantization, gain, bias, temporal correlation and packet processing must enter
the recorded-data model or be reported as unresolved assumptions.

## Next gate

Define a common, motion-based support policy and a precise acceleration
observable before applying the diagnostic to recordings. Qualify calibration,
quantization and time association, then combine trajectory approximation,
receiver uncertainty and acceleration uncertainty consistently. Do not import
fused attitude or choose a window by which model wins.

The main **53 globe / zero flat / zero unresolved** result is unchanged. This
work still does not isolate the real gyro contribution or calibrate significance.

[Complete matrix and averaging tables](README.md) ·
[All candidate/window data](trajectory-candidates.csv) · [Next-stage requirements](NEXT_PLAN.md).

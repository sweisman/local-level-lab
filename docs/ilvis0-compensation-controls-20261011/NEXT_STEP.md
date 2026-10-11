# Qualify the corrected integration beyond the first control

The [completed comparison](FINDINGS.md) identifies an integration/calibration
interaction in noise-free software controls. It does not authorize new NASA fits.
Preserve this report and the original predictor. Extend qualification in a separate
module and freeze; do not alter a completed study's dependencies.

## Next bounded software check

Test independent constant-latitude tracks away from the equator, including both
hemispheres. Generate ordinary body-rate and specific-force integrals from continuous
motion, with the correct local transport vector and independently timed receiver
positions. Cover the two globe models and the stationary disc equally. Retain the
existing six-parameter region and solver so a changed physical control does not
also change the optimization method.

Before fitting, verify predictions at known calibration and their derivatives.
Include roll, unequal packet spacing, interior and near-boundary calibration, and
more than one starting point. These checks should establish whether the improvement
survives different motion and geographic geometry. They cannot establish raw sensor
noise performance or identify the archive's preprocessing.

Separately generate a precisely defined already-compensated increment control from
independent continuous integration. Check its appropriate predictor and demonstrate
the error introduced by double correction. Preserve the explicit convention guard.
Do not label either convention as Applanix's without supporting evidence.

Freeze identities and a finite numerical allowance before launching the extension.
The completed nine-start allowance cannot be reused. Later tests of noise, longer
duration and all 27 nuisance parameters need their own scoped controls and meaningful
prediction/calibration criteria; agreement in a weak direction is not unique recovery.

## Return to the recordings

Once these checks pass, prepare a small matched observed comparison with both
integration alternatives, unchanged raw measurements and equal physical bounds for
all three models. Record the increment-convention assumptions explicitly. Keep clock
choice separate, so an improvement can be attributed to the changed integration.

Use complete preselected stretches; retain unfinished fits and inspect objective,
prediction errors, Z gain/offset, other active limits and residual correlation. Prefer
no model because its implementation was tested more favorably. A separately approved
finite allowance is required before those observed fits. Continue to interpret shape
first and rotation only after a complete globe result. No archive-wide rerun or
statistical promotion follows automatically from the software controls.

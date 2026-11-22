# Match Doppler-derived acceleration to the logged iMAR force

Use the first 400 reports of the sealed ESA 400/120 cut. Divide them
into 16 consecutive blocks of 25 reports. Use their fixed centers
and two symmetric stencils of 11 and 25 reports. At each center fit
quadratic geographic coordinate rates from each of the three velocity
sources. Use one position at the center from the receiver export and
integrate the polynomial rates within the stencil. GPS and GLONASS
Doppler use the same local coordinate frame as the exported velocities.
No receiver position is differentiated.

The derivative of the velocity fit is a weighted average of acceleration.
Apply its exact nonnegative piecewise-constant time kernel to the logged
iMAR acceleration magnitude and to the magnitude required by each
candidate path. Read only the saved velocity increments and clock intervals
from the sealed inertial record. Use the recorded clock and hold each
sample's magnitude over its logged interval. No gyro, fused attitude or
Earth-model fit enters the calculation. Use the existing force predictions
for specified-field globe, still globe, still disc and the matched-field
disc control. Compare fixed gravity of 9.81 m/s² with one shared
height-dependent correction anchored at the first earlier position.

Report candidate contrasts, receiver and stencil differences and the fit
to logged force magnitude. For each setting estimate one constant offset
as the median residual of its first eight blocks. Apply it to the final
eight. Report all settings equally. The offset is a descriptive correction
and supplies no guarantee about sensor calibration. The final eight blocks
are an internal check on this flight. These are all prior training reports
in the original Earth-model study.

Freeze the source and environment before reading the inertial increments.
Use one numerical thread, at most 155,868 sealed inertial intervals, 96
velocity reconstructions on stencils and 768 matched force predictions.
No new Earth-model fit or forecast, later 120 records in the calculation,
or reserved flight groups. This feasibility check supplies neither an
absolute receiver error bound nor an aircraft decision rule.

[Doppler motion comparison](ESA_DOPPLER_COMPARISON_RESULT.md) ·
[Previous time-matched force comparison](ESA_MATCHED_FORCE_RESULT.md)

# First matched inertial forecasts on the two prepared recordings

Run one equal-budget start for each of the four geometry and field
combinations on each prepared recording. The eight starts use the
nominal 200 Hz clock, the unsubtracted-increment case, a ±1°/hour
gyro-offset limit, and wider arithmetic. These are the settings for
checking the recorded input and forecast path. Other clock, processing
and offset assumptions belong to the separately frozen comparison.

Fit only the earlier onboard receiver coordinates using the existing
working receiver weights with correlated horizontal and vertical errors.
These are fixed development weights. They do not assign a probability to
the resulting forecast errors. Use the same weighting and starting rule
for every model. Preserve the physical initialization and all active
calibration parameters.

For each start allow up to 30 training evaluations and one forecast,
with a 30-minute cooperative wall limit across four single-thread
workers. Check the native values and wider arithmetic against the
source freeze. Save the forecast before opening the later positions.
Verify that the forecast reproduces the training prefix within
0.00000001 m and score the later path against each of the three GPS
streams. Record numerical stopping and forecast error separately.

The run requires the passing generated wider-arithmetic gate, the
two prepared input receipts, exact software qualification, and
qualified task recovery. It is retrospective development. It does
not certify aircraft coverage or decide Earth shape.

[Prepared input scope](MATCHED_OBSERVED_PREFLIGHT_PLAN.md).

# Fixed calibration-swap diagnostic

## Question

Two preselected recorded-data receiver cuts produced later paths that differ
by 0.752 m and 0.320 m between saved numerical solutions. The
[timing check](OBSERVED_FIXED_ENDPOINT_RESULT.md) replayed all eight fixed
points exactly. Which groups of fitted calibration parameters can account
for the path differences when changed **without refitting**?

This is a numerical sensitivity diagnostic for one specified-field globe
candidate. It does not compare Earth models, establish a correct calibration
or revise any fit's stopping label.

## Frozen inputs and parameter groups

Use exactly the two maximum-disagreement inner-cut pairs recorded in the
[sealed diagnosis](observed-method-v2-diagnosis.json): the trust-region and
SciPy TRF start-1 solutions on the 2010 northern recording, and SciPy TRF
starts 0 and 1 on the 2015 southern recording. Use the original complete
training inputs, parameter bounds and receiver/IMU clock. Keep all later
receiver positions unavailable to the evaluator.

The 26 normalized calibration coordinates form four disjoint groups:

1. Receiver/IMU time offset.
2. Vertical inertial calibration: gravity correction and Z-axis gyro and
   accelerometer biases and gains.
3. Horizontal inertial calibration: X/Y gyro and accelerometer biases and
   gains.
4. Initial state and mount: attitude, velocity, position and lever arm.

For each pair, use each solution as an anchor. Calculate its unchanged
baseline, four one-group swaps from the counterpart, and a full-vector swap
as an exact counterpart control. This gives 2 pairs × 2 anchors × 6 variants
= **24 fixed vectors**. No optimizer runs. Each vector gets one charged
training residual/tangent calculation and one charged continuous forecast.
Report training cost and later-path distance to both saved reference paths.
The saved paths are forecasts, not later receiver measurements.

## Finite execution and recovery

Freeze the complete source/input/environment hash and exact task identities
before launch. The total cap is 48 native calls and 880,988,220 packet visits,
using four one-thread workers and a cooperative one-hour wall limit. Charge
before every native call; retain all failed vectors and results. Qualify
task-level reboot recovery before launch. An interrupted task needs a new
finite recovery stage, while sealed tasks may not run again.

## Interpretation

The two swap directions expose interactions: the effects of separate groups
need not add up to the full-vector change. A group that shifts a fixed
forecast is a sensitivity finding, not proof of its physical calibration.
If neither single group explains the path split, investigate combinations
and weak directions under a separately frozen plan. Any changed numerical
stopping rule still needs independent generated qualification and a fresh
recorded-data study. The earlier 80 fits, this 24-fit pilot and the 53-stretch
model comparisons keep their saved labels.

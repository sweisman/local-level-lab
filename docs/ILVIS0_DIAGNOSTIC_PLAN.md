# Diagnostic requirements

The main comparison is complete: **53 globe preferences, zero flat preferences
and zero unresolved stretches**. This page defines the checks needed to strengthen
that result; it is not a list of unfinished main-analysis fits.

An **IMU (inertial measurement unit)** measures angular motion and specific force.
The analysis uses recorded IMU increments and primary-receiver positions, not
the instrument's fused navigation answer.

[Current findings](CURRENT_STATUS.md) · [Execution order](NEXT_STEPS.md) ·
[Technical roadmap](ANALYSIS_ROADMAP.md).

## Evidence already available

| Question | Completed evidence | Still needed |
|---|---|---|
| Do all selected model comparisons pass their numerical checks? | All 53 main full-position comparisons now pass their required model/case, control and repeat checks. | Separate qualification for new objectives and observation models. |
| Does preference survive a different clock convention? | All six matched refits completed and preserved globe/field preferences. | Independent support for the physical integration interval and its calibration interaction. |
| Does the horizontal score retain separation? | All 36 saved-parameter comparisons favor globe; one of two refitted stretches passes every repeat and favors globe. | A physically adequate comparison when height is not scored; the other sensitivity stretch remains unresolved. |
| Did a timing grid resolve that sensitivity stretch? | Both controls and 37/38 fits passed individually. | Four selected repeat comparisons still fail; wider searches are deferred. |
| Can sensor channels simply be removed? | Twenty-five software controls expose the missing orientation/force constraints and define a force-magnitude diagnostic. | Independent trajectory and uncertainty qualification before recorded-data use. |
| Are prediction and uncertainty validated? | Residual audits and split-recording trials provide development evidence. | Complete withheld prediction and calibrated coverage with shared-flight accounting. |

## 1. Investigate clock and joint calibration

Preserve the [clock evidence](ilvis0-clock-audit-20261011/README.md),
[matched refits](ilvis0-clock-trial-20261010/README.md) and
[calibration profiles](ilvis0-z-followup-audit-20261012/README.md).
Do not confuse packet timestamps with the duration represented by an increment.

Any new sensitivity grid must compare all candidates with matched bounds,
initialization and error assumptions. Report joint gain, bias, gravity and timing
trade-offs rather than interpreting a small fitted error as unique calibration.
Exact proprietary device records are supporting evidence, not a blanket
prerequisite for proceeding.

## 2. Establish a shared residual-error model

Use epoch-level residuals to assess autocorrelation, cross-axis dependence and
low-frequency structure. Develop the covariance model on training data, then
check predictions on observations excluded from nuisance and covariance fitting.

Small whitened training RMS is not a calibrated uncertainty statement. Include
parameter-estimation uncertainty and account for nonlinear bounds or report
their unresolved influence. Numerical controls do not establish empirical coverage.

## 3. Identify the measurement contribution

The [channel-control requirements](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md)
now define the next implementation stage:

- Qualify force calculations using independent generated motion under all three
  physical candidates.
- Specify differentiation of receiver trajectories and propagate its uncertainty.
- Keep acceleration calibration, gravity and coordinate assumptions explicit in
  the acceleration-magnitude comparison.
- Never supply fused attitude in place of omitted gyros, or use omitted
  acceleration measurements to initialize tilt.
- Freeze a finite matched recorded-data comparison only after qualification.

The completed horizontal-only work remains a score sensitivity check. Its large
unscored height errors prevent treating it as a valid full-flight reconstruction,
a gyro-only test or proof of altitude/datum independence.

## 4. Qualify optima, prediction and independent replication

Require fresh numerical checks and independent starts appropriate to each new
objective. Preserve the original model/case and repeat gates; a visually convincing
ranking does not override a failed calculation check.

For prediction, fit calibration only on declared training observations. Keep
withheld time blocks or independently supported flight/installation groups out
of optimization and covariance selection. Report failures and abstentions.

Group overlapping recorder streams and shared flight intervals. Matching a
configuration identifier is not proof that two recordings share a physical unit
or a stable installation.

## 5. Rotation-field work follows these checks

The [field study](ROTATION_FIELD.md) will estimate size and direction freely,
then test geographic patterns and rate. Check identifiability against calibration,
transport and unknown onboard removal before fitting the field.

The main fixed-rate comparison has not distinguished solar from sidereal rate.
Longer [ESA/Wuhan sources](external-imu-data/README.md) require separate eligibility
and observation qualification; neither has entered the Earth-model comparison.

The earlier [detailed diagnostic history](DIAGNOSTIC_HISTORY.md) preserves the
development record, completed controls and historical trial outcomes.

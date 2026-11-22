# Changing-gyro-bias error-law development

## Question

Can a fixed Gaussian error law that explicitly includes changing gyro bias
cover later position errors from independent generated IMU and receiver
histories? The first [eight-case pilot](integrated-drift-pilot/RESULT.md)
remains sealed. This is a new development candidate, not a correction to its
outcomes or a claim about an observed aircraft.

## Physical approximation

The generator's gyro-rate bias is a random walk. Its integrated attitude
error changes the direction of the measured gravity force. Over a short
interval, the resulting horizontal acceleration error has a changing
derivative. Add a third-order position-error driver: white **snap** driving
the jerk-error state. Retain independent white acceleration, white jerk,
receiver random walk and per-report receiver error. Use one transparent
15-state north/east/up model: position, velocity, acceleration, jerk and
receiver offset. The approximation ignores detailed changing attitude,
axis coupling and non-Gaussian or unknown aircraft effects. It must pass
generated checks before any observed use.

## Implementation and checks

1. Add `analysis/lll/integrated_drift_v2.py`, leaving the first candidate's
   frozen source unchanged. Require every process scale and initial-state
   uncertainty as an explicit input. Build the exact continuous-time
   integrated white-noise covariance for acceleration, jerk and snap; do not
   add a numerical floor. Reuse `LinearInnovations` for earlier-only
   conditioning.
2. Add focused tests with independently integrated dense covariance,
   conditional prediction, zero-snap reduction, invalid inputs and bounded
   storage. Run them with the repository's numerical allocation guard.
3. Freeze a small new-seed generated pilot before scoring. Use the same
   source-independent analytic motion generator and measured-increment
   propagator, but no first-pilot seed. Set the snap intensity from the
   generator's declared gyro-bias diffusion before viewing new outcomes.
   Save forecasts before later scores. Count whole histories, not epochs.
4. Score both 95% marginal intervals and a predeclared conservative
   simultaneous 95% bound across all later coordinates. Preserve all misses
   and numerical failures. A small pilot can reveal implementation or
   adequacy problems; it cannot calibrate aircraft coverage or promote the
   law. A larger calibration/validation design must be frozen separately.

The seven reserved ESA flight groups and all existing frozen studies stay
closed. The observed development recording may be used only after generated
software and accuracy gates have passed under a separately frozen plan.

The new operator's four focused tests pass: independent continuous-noise
quadrature, earlier-only conditional prediction, exact reduction to the first
candidate with snap absent, and fail-closed inputs/storage. The
[fresh-seed pilot](integrated-drift-v2-pilot/RESULT.md) then closed all 16
tasks. Every generated history stayed inside the predeclared conservative
simultaneous range; 10/16 stayed inside every nominal marginal range. This
checks a small generated cohort, not aircraft coverage. A separately frozen
larger cohort is the next statistical gate.

That [independent 256-case check](integrated-drift-v2-validation/RESULT.md)
closed all technical tasks but failed its frozen gate. Four of 128 vibration
histories exceeded the simultaneous bound; none of 128 without vibration did.
The final bound's median per-coordinate half-width was 25.59 m. The result
does not establish vibration as the cause, because the two strata used
different noise seeds. Saved-data diagnosis can locate the misses; any
changed physical law needs new seeds and a separate freeze.
The [saved failure diagnosis](integrated-drift-v2-validation/VIBRATION_DIAGNOSTIC.md)
places three maxima at the first withheld second and one at second 69.
An independent [clean 100 Hz control](integrated-drift-v2-validation/CLEAN_PROPAGATION.md)
finds integration error under 0.0004 m in both motion modes, too small to
explain the 0.15–0.67 m missed predictions. The separate
[matched-noise control](paired-vibration-control/RESULT.md) found at most a
0.000224 change in standardized score when toggling this generator's 10 Hz
vibration. At integer-second receiver reports the position perturbation
repeats as a constant 0.2 mm offset. This control does not explain the
earlier four-versus-zero split. A new motion
control that remains visible after receiver sampling and an interval-
usefulness check are next; the failed coverage gate remains unchanged.
The [receiver-visible 0.37 Hz pilot](nonaliased-motion-control/PILOT_RESULT.md)
then passed all 16 matched-noise pairs, with no range misses and at most
0.0016 paired change in maximum standardized error. The generated coverage
gate remains failed. An [endpoint width check](INTERVAL_USEFULNESS.md) shows
that single-coordinate ranges with 25.59 m half-widths would need centers
more than 51.18 m apart to be disjoint. The full model-contrast usefulness
test and tail-coverage calibration are still open.
The separate [fresh 256-history check](threshold-42-validation/RESULT.md)
then tested a 4.2 threshold chosen after the first gate failed. All technical
tasks completed; 1/128 histories without vibration and 0/128 with it exceeded
the new range. Its exact per-stratum bounds pass the frozen generated gate,
with a 29.57 m median endpoint half-width. The earlier gate stays failed.
This is simulator coverage, not aircraft coverage or a model decision.

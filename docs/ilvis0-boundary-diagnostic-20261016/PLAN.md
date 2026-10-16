# All-six timing-boundary diagnostic

The six unresolved stretches contain eleven unfinished primary fits and eight
unfinished repeats. Saved diagnostics place these near clusters of IMU packet
transitions. The smooth stopping calculation can cross a transition and worsen
the prediction even when the endpoint appears locally settled.

This study checks whether a qualified two-sided numerical rule resolves that
specific problem. It is a diagnostic, not a new Earth-model campaign.

## Qualification and scope

The [adapter qualification](../ilvis0-boundary-adapter-qualification-20261016/RESULTS.md)
passed thirty software controls. Two additional
[native callback controls](../ilvis0-boundary-native-qualification-20261016/RESULTS.md)
passed using the actual compiled integrator and independently specified motion.
The earlier exact-knot policy passed forty-three controls. These software checks
do not establish observational uncertainty or a scientific detection threshold.

- Exactly twenty-one identities: nineteen unfinished endpoints and two passing
  smooth controls. Run both controls first. If either fails, leave the nineteen
  timing searches unstarted.
- Nineteen time-only optimization starts maximum; zero joint nuisance-fit starts.
  The three already-converged smooth repeats remain untouched.
- At most twenty-six native evaluations per identity, **546 total**, no retries.
  Failed or interrupted starts and calls remain charged.
- One worker, four total numerical threads, zero reserved threads. At measured
  native speeds the full allowance is approximately two to three hours.
- Source, inputs, retained-original hashes, numerical environment and exact
  identities are frozen before launch. Preserve every earlier result.

## Procedure

Reconstruct each saved problem without changing the selected interval, physical
model, covariance, calibration bounds, processing hypothesis or nominal 200 Hz
integration clock. Reproduce the saved objective and repeat the original point.

For an unfinished endpoint, enumerate every distinct representable packet
transition within one microsecond. Clock enumeration has a 200,000-query limit;
adjacent-interval verification has a separate 1,024-query limit per identity.
Use at most twelve native gradient samples to locate an adjacent negative-to-positive
timing-gradient crossing. Interior gradients need not be monotone; this finds a
local crossing, not a global optimum. No bracket means abstention.

Hold every other parameter at its saved value during timing location. Verify
the selected transition and its adjacent packet intervals, and require the
relocation to preserve objective and physical predictions within the established
numerical limits. Then apply the ten-call two-sided check, releasing all nuisance
directions in both branch corrections. Neither damping nor a reduced nuisance
space can substitute for that check. An unchecked neighboring boundary abstains.

The smooth controls retain their saved points and original smooth stability rule.
Preserve the 10^-4 stationarity, 10^-8 relative cost, 1 mm axis RMS and 1 cm maximum
position-change limits. These are numerical tolerances, not sensor specifications.

## Interpretation and artifacts

Publish old and proposed timing, objective, physical prediction changes, both
branch checks and charged calls. Save the selected residuals and all Jacobian
columns for subsequent diagnosis without more integration. Keep original failure
labels and the current 47 globe / zero flat / six unresolved tally unchanged.

A successful diagnostic alone cannot relabel a stretch. All model/case companions,
scheduled repeat agreements and controls must be checked before a separate
numerical recovery publication. The three smooth repeats in different timing
basins may require a subsequent finite profile with nuisance reoptimization.

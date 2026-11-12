# Receiver-window support policy

This software gate chooses the receiver observations used to estimate local
motion for the acceleration-only diagnostic. It does not read an aircraft file
or compare Earth models.

The caller supplies ordered receiver times, reported ground speed and course,
and vertical rate. Those quantities describe the observed aircraft motion.
The caller also supplies a versioned policy: candidate symmetric half-windows,
maximum sample gap, minimum sample count and speed, and maximum changes in
course, speed and vertical rate. It also gives a maximum plausible speed.
No threshold is inferred from a gyro stream,
fitted residual, preferred model or later prediction result.

For every candidate window, the selector records its bounds, motion spans and
accept/reject reason. It chooses the **longest accepted** candidate to reduce
derivative noise while avoiding declared maneuver limits. If none passes, it
abstains. One selected window must be reused for all physical candidates; a
model cannot choose the window that makes it look best. A training-only caller
must pass only its training observations.

The policy is a support rule, not a proof that a local polynomial approximates
the true aircraft path. Receiver course and speed can themselves be noisy or
come from a geodetic chart. The later recorded-data study must freeze threshold
values, their source and the exact receiver stream before reading original IMU
increments, and must keep rejected windows visible. It must combine polynomial
truncation, receiver covariance, clock, acceleration calibration, quantization
and finite-packet averaging before making a channel-contribution claim.

For the Applanix `.013` receiver stream, VTG course and speed sentences have no
UTC field. Their packet order is preserved, but they cannot be assigned to GGA
epochs by an assumed time offset. A recorded-data adapter must either justify
the association separately or derive motion from the timestamped receiver
positions under an explicit coordinate convention.

The adapter takes primary-receiver GGA fixes with a ZDA-checked
`utc_week_s` measurement time and estimates speed, course and climb rate from
adjacent fixes at those times. The enclosing Applanix packet's `time1_s` is
not substituted for the GGA measurement time. Ellipsoidal height is formed from
the recorded GGA orthometric height plus its recorded geoid separation; a
missing component rejects the fix. It uses
the WGS84 coordinate metric only to screen aircraft motion; these derivatives
are not independent evidence for a globe. It handles longitude wrap, rejects
unordered, incomplete or over-gapped fixes under an explicit gap limit, and
never assigns a time to VTG or interpolates
a missing fix. Its endpoint estimates use one interval, so a later error budget
must account for their greater noise.

Implementation: `analysis/lll/ilvis0_receiver_support.py`. Tests:
`analysis/tests/test_ilvis0_receiver_support.py`.

The follow-on receiver-trajectory bridge applies the chosen window to the
joint local-polynomial derivative operator. It unwraps longitude within that
window, so an excluded earlier fix cannot shift its coordinate chart. The
bridge accepts a supplied full coordinate covariance and returns its local
slice with the derivative estimate; that covariance is still an assumption,
not a calibrated receiver-error law. All six focused bridge checks pass,
including the end-to-end selected-window regression. It has not selected or
fitted an archival interval.

## Implementation steps

- [x] Add an immutable `SupportPolicy` with explicit limits and a pure
  `select_support` function. Inputs are receiver kinematics only; output retains
  every candidate and an abstention when all fail.
- [x] Test irregular timestamps, gaps, sample scarcity, circular course wrap,
  low speed, maneuvers, deterministic longest-window choice and input immutability.
- [x] Run the focused tests. Keep recorded-data use blocked until the separate
  timing and observational-error gates qualify.
- [x] Derive screening motion from timed GGA positions without an assumed VTG
  time association; test chart scaling, date-line wrap and malformed fixes.

All 21 focused software checks pass, including the dated Applanix GGA mapping
and cases where packet and GGA
measurement times differ. No threshold has been selected for an
archival recording, and no recorded interval has been selected or fitted by
this policy.

The earlier recorded acceleration-only checks used fixed receiver windows.
Their selected observations, outcomes and source freezes remain unchanged;
this selector belongs to a separately frozen follow-up.

[Channel requirements](CHANNEL_CONTROLS.md) ·
[Error-budget findings](../ilvis0-channel-error-budget-20261019/INTERPRETATION.md).

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

A subsequent [joint receiver-only bridge](../../analysis/lll/ilvis0_joint_receiver_force.py)
uses that selected support for all three candidate force calculations. Five
focused checks pass, including covariance shared across candidate models,
overlapping windows and all-window
abstention. It has not selected a recorded interval or calibrated receiver
error.

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

The structured bridge now also accepts saved primary-receiver enhanced-position
records. It uses their GPS week/millisecond measurement times and their own
north/east/up velocity for motion screening. It keeps this source labeled
separately from NMEA GGA and from fused Group 1 navigation. Three new checks
and the existing support/bridge checks pass. The receiver's reported precision
is still not a calibrated error law, and no recorded block has been fitted by
this new path.

The [receiver-only window study](../ilvis0-receiver-support-inventory/README.md)
then froze a 5/10/15-second support rule and applied it to the 52 decoded
stretches. It accepted 2,194 of 2,365 target times. Every rejected target
exceeded the stated receiver vertical-rate variation limit in all windows.
This is a completeness and motion screen; it has no IMU observation or
Earth-model outcome.
The [saved threshold-margin audit](../ilvis0-receiver-support-inventory/MARGIN_AUDIT.md)
finds 398 chosen windows within 0.10 m/s of that vertical-rate limit. It
describes closeness to one rule, not measured velocity error or calibrated
selection stability.
The [eleven-pair receiver check](../ilvis0-receiver-window-pairs/README.md)
compares the fixed rule at 490 common times. Both receivers accepted 456,
both rejected 27 and disagreed seven times. This tests relative repeatability;
shared receiver errors and absolute window-selection error remain unmeasured.

The [sealed 53-stretch gap inventory](../ilvis0-receiver-gap-inventory/README.md)
reports every original receiver row range before window selection. Fifty-two
saved primary-receiver streams each form one block under the 1.5-second rule;
the remaining strict-decoder failure is retained. The splitter does not fill
gaps or count separate blocks as independent flights. The later matched study
must retain this ledger and qualify receiver-error assumptions.

### Keeping training and later force windows separate

The two prepared aircraft recordings share their GPS epochs with the
[saved force comparison](GPS_FORCE_COMPARISON_RESULT.md). An audit of the
full support of each window found the following split. A window belongs to
training or later scoring only when all its GPS fixes belong to that side.

| Recorder | Window | Training | Later scoring | Crosses the cut |
|---|---:|---:|---:|---:|
| IMU8 | 10 s | 435 | 213 | 10 |
| IMU8 | 20 s | 425 | 203 | 20 |
| IMU8 | 30 s | 415 | 193 | 30 |
| IMU21 | 10 s | 285 | 138 | 10 |
| IMU21 | 20 s | 275 | 128 | 20 |
| IMU21 | 30 s | 265 | 118 | 30 |

To reproduce the check, verify the window table and the prepared `training.json`
and `scoring.json` files against their recorded hashes. For each `evaluated`
window, use its `first_used_tag` and `last_used_tag` to find the inclusive
range in the combined `gps_tags_ms` and verify the target is present and
the count equals `sample_count`. Count whether the last fix is before the
cut, the first fix is after it, or the support crosses it. All 3,213 evaluated
windows matched by tags and count. The 123 unsupported windows stay excluded.
The [position receipt](gps-force-comparison-receipt.json) and [prepared input
receipt](matched-observed-inputs-receipt.json) identify the same GPS parent.

This gives the gyro-free study 680 training windows and 311 later windows
at 30 seconds, with 60 crossing windows excluded. Adjacent windows overlap,
so their force errors are correlated. The audit used only window and epoch
metadata. It leaves the matched accelerometer calculation and uncertainty
qualification open. A [follow-up packet audit](MATCHED_FORCE_SUPPORT_RESULT.md)
now identifies the whole accelerometer packets retained under both clocks
and the full timing allowance for all 991 windows.

The continuous-force helper now encloses the predicted mean over each
contiguous packet interval. It divides the time support into sections, shifts
each section by the allowed clock offset, and propagates the fitted quadratic
GPS path and its derivatives through the force equations. A vertical known
answer and independent quadrature for all four candidates pass. The bounds
apply to the supplied path and leave real receiver error, trajectory model
error and calibration outside their scope. [Implementation](../../analysis/lll/ilvis0_force_support_average.py) ·
[Checks](../../analysis/tests/test_ilvis0_force_support_average.py).

## Next qualification for the matched comparison

Receiver error can change both the chosen window and the force inferred
from it. Test those effects together on independent generated paths,
including paths near the existing window limits. Apply one perturbation to
the whole receiver record and reuse it for all four candidates. Keep the
correlation across fixes and windows, and count a change to or from
abstention in the comparison.

Use a common fixed-window comparison to check the uncertainty calculation
before assessing the adaptive rule. The adaptive calculation must retain
every window that could be selected under the stated error range, including
cases with no usable window. Check the resulting force ranges against known
motion and measured accelerometer directions. Without an independent
attitude or rate bound, the primary gyro-free control must permit all
orientations consistent with the force observations. Report model
distinctions only when they survive that ambiguity and the declared
uncertainty. A generated pass establishes software behavior under the
tested error laws. Aircraft error and any added motion limits need separate
support before the recorded pilot.

The first software check uses timestamped GGA. In
`analysis/lll/ilvis0_adaptive_force.py`, translate supplied latitude,
longitude and height bounds into conservative screening-error ranges. Carry
all possible longest windows into the existing polynomial and force-bound
calculations. Use one joint covariance projection for every window and
candidate. The deterministic force bounds include polynomial truncation
and coordinate error separately from that linearized covariance.
`analysis/tests/test_ilvis0_adaptive_force.py` checks a stable fixed-window
case against analytic force for all four models and a smooth height error
that changes the chosen window. These are short, deterministic software
checks with zero IMU-fit starts.

### First known-answer results

On an analytic eastbound track with constant latitude, the stable window
reproduced the four independently calculated force magnitudes. In a second
case, a smooth coordinate error of at most 0.109 m in height changed the
selection from an eight-second window to a four-second window. The error
bound kept both windows and the possibility of abstention. Both sets of
force ranges contained the known force for every model. The four-second
ranges were about 0.25 m/s² wide, and the eight-second ranges were about
0.065 m/s² wide. The four exact model predictions spanned about
0.067 m/s² in this example, and the ranges overlapped.

The [software checks](../../analysis/tests/test_ilvis0_adaptive_force.py)
verify that the joint calculation matches a dense covariance reference and
preserves correlation between the alternative windows. They also cover
missing support and smooth coordinate errors through the date line. The
code retains the supplied error box and covariance separately. The bounds
allow some combinations of window choices that may be impossible under a
shared position-error history, so they can be wider than necessary.
The 0.109 m bound is specific to this generated case. It does not measure
archival receiver accuracy or establish prediction coverage.

### Shared accelerometer calibration

The [calibration search](../../analysis/lll/ilvis0_adaptive_calibration.py)
uses one box of accelerometer gains
and offsets for the entire history. It rejects a box only when some target
that must have a window is incompatible with all of its possible windows.
All four models get the same box budget. A calibration whose force
magnitudes overlap at every required target is compatible with the scalar
ranges. A search that exhausts its budget is unresolved. Compatibility
leaves joint position errors, time-varying orientation and physical adequacy
open.

All eight moving known-answer checks retained their generating model under
one injected accelerometer calibration, with exact heights and with a
smooth height error of up to 0.08 m. These checks used all four model
geometries and fields, with changing body orientation. In a separate clean
control with very tight calibration limits, the scalar test separated
the generating model from all three alternatives. Another control excluded
a model whose individual targets could each be matched only by choosing
inconsistent calibrations. When GPS error could remove every selected
window, the calculation abstained.

The next observational check must establish how much position error the two
receivers could share, and how that error changes the force estimates.
The [eleven receiver pairs](../ilvis0-receiver-overlap/recorded-study/README.md)
identify receiver disagreement. An error that moves both reported paths
together cancels in their difference. The [shared height-error calculation](SHARED_GPS_ERROR_RESULT.md)
tested that case on the saved paired epochs and retained the same-field
force ordering at every sampled phase. This leaves the amplitude of the
real error open. The next receiver-only check is to inventory usable satellite
measurements and orbits for the eligible stretches. Keep the recorded IMU
comparison gated on defensible position, timing and calibration bounds.

[Channel requirements](CHANNEL_CONTROLS.md) ·
[Error-budget findings](../ilvis0-channel-error-budget-20261019/INTERPRETATION.md).

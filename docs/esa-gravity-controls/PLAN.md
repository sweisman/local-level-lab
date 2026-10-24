# Checking gravity during climbs and descents

## Why this check is next

The [ESA prediction pilot](../esa-development-pilot/README.md) fits earlier
positions closely for the specified-field globe candidate but misses later
height. The [saved-data diagnosis](../esa-development-diagnosis/README.md) finds
calibration at bounds and shows that gravity variation over the recorded height
range could matter. Neither observation establishes the cause of the errors.

This is a software check on generated measurements. It opens no aircraft file,
changes no existing result and cannot establish an Earth-model preference.

The shared gravity extension now passes 19 focused native checks, and the affected
native/compensation regression set passes all 45 checks. Independent truth and
related generated-control regressions pass all 95 checks. The longer 48-case
study has not run; these short checks do not qualify
a revised observed-data fit.

## Physical alternatives

Preserve the existing constant-gravity calculation and its interface. Add an
explicit alternative in the shared predictor and tangent calculation:

`g(h) = g_anchor × ((6,371,000 + h_anchor) / (6,371,000 + h))²`.

Here `h` is the **predicted** height at the integration midpoint. The anchor
height is fixed from the initial observation; its magnitude retains the same
constant adjustment and bounds as the original model. No later receiver height
may enter a forecast. This adds no freely varying gravity or drift parameter.

Apply the same declared height dependence to all three geometry candidates.
It is a common force-law sensitivity, not independent evidence for curvature.
Latitude dependence, gravity anomalies and other missing dynamics remain outside
this first check. Keep the initial force-based reference distinct from measured
gravity during aircraft motion.

## Implementation and independent checks

Extend shared library components rather than copying a study worker or motion
kernel. Keep old entry points on their original constant mode. Historical studies
continue to use their archived source, never the revised implementation.

Before a numerical study, run focused deterministic checks covering:

- Exact preservation of the constant-mode output and Jacobian.
- Constant-height limits, gravity signs, dimensions and invalid inputs.
- Midpoint gravity evaluated from predicted state, including its derivatives.
- Every original calibration column, including height, gravity and time offset.
- C value predictions agreeing with the C++ derivative calculation, and full
  central-difference checks on short generated tracks away from query boundaries.
- Known-answer vertical motion and an independent Cartesian aircraft generator.
  Truth generation must not call the predictor or its gravity helper.

## Finite generated study

Freeze source/environment hashes and passing software checks before launch.
Use 48 identities: three candidates × latitude ±55° × removal 0 or 0.35 ×
constant or height-dependent gravity × two motion patterns. Both patterns last
1,200 seconds and span 2 km in height; one climbs and turns, the other descends
and reverses its heading evolution. Use the existing analytic `fast` body-motion
pattern. Height is `2500 − 1000*cos(pi*t/1200)` metres for the climb and
`2500 + 1000*cos(pi*t/1200)` for the descent, with analytic first/second derivatives.
Mirror the northward coordinate oscillation for the descent while retaining the
eastward course progression. The anchor height is 1,500 m or 3,500 m respectively.
The independent Cartesian generator derives all force/rate channels without
calling the native predictor or its gravity expression.

Each identity uses known, nonzero sensor/antenna corrections and initial state.
Use the existing positive calibration sign in northern cases and its negative
counterpart in southern cases; neither is an instrument specification.
Generate the same physical trajectory at 300 and 600 Hz. Evaluate 39 fixed queries
at `30 + 30*j + 0.001` seconds, for `j = 0..38`, retaining every increment.
Run the value predictor at both rates and the complete tangent predictor at
300 Hz. That permits **144 native calls**, 2,695,680,000 packet/query visits,
zero optimization starts and no retries. Reserve calls and construction work
before execution. Four workers use one numerical thread each, with a cooperative
one-hour ceiling. No unused allowance from earlier work is available.

At both resolutions the generated acceptance screen uses the geographic adapter's limits:
horizontal and height RMS at most 1 m, maximum spatial error at most 5 m, plus
the previously declared linear-point refinement rule. Value/tangent predictions
must agree within 0.001 m. Report failures rather than relaxing these limits.

## What this can qualify

Passing qualifies the tested gravity mechanization with known initialization and
calibration. It does **not** qualify a new observed fit. Longer training-only
calibration and forecast controls, with both working receiver-error cases and all
nuisance columns, remain a separate gate. Only then may a separately frozen
comparison reuse the original development interval under unchanged accuracy limits.

All seven ESA confirmation groups and the original 53-stretch result remain
protected. No calibrated confidence, field cause or sidereal/solar conclusion
follows from these controls.

[Implementation](IMPLEMENTATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md).

# What comes next

**The main comparison is complete: all 53 selected stretches fit globe geometry
better than the tested flat-disc model.** All also favor the model with a
specified background rotation signal over zero. This does not yet give a tested
statistical confidence level or identify the signal's cause.

An **IMU (inertial measurement unit)** records turning with gyroscopes and
specific force with accelerometers. The gyroscope records are central to this
study; receiver positions help constrain the reconstructed flight.

[Current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

<a id="then-strengthen-the-interpretation"></a>

## Now: make prediction tests meaningful

A good fit uses observations it has already seen. The stronger test is to fit
one part of a recording and predict another part without using those later
measurements to adjust the answer.

Before doing that, we need reliable **error ranges** around the predictions.
The present calculation is too conservative: it allows ranges too wide to be
useful over a full recording. Recent improvements helped, but have not solved
this problem. These wide ranges are not measured aircraft errors.

Prediction widths meet the target in four of six groups. Both specified-field
globe groups still miss it. A follow-up checked 36 extreme error combinations:
none survived recomputing all the errors from one calibration. The calculation
therefore needs to keep those errors coupled. This has not yet produced a
qualified narrower range, so new aircraft prediction fits remain gated.
[Latest diagnostic](ilvis0-calibration-map-diagnostic/INTERPRETATION.md).

The [source-reference check](ilvis0-source-reference/INTERPRETATION.md)
passes all six generated groups and reduces the relevant vertical error
allowance by 68–69%. The next step is to carry that gain through the dynamic
calculation without losing training-derived information.

The [cached transport implementation](ilvis0-cached-transport-controls/INTERPRETATION.md)
now passes all 24 controls under the same numerical and time limits. Next is
connecting the tighter body-source interval at the correct packet prefixes.
Complete prediction and aircraft-validation gates remain open.
The [streamed source rows](ilvis0-source-stream-controls/INTERPRETATION.md) now
pass every midpoint/end check. The [six-source screen](ilvis0-transport-range-preflight/README.md)
finishes with four compatible bounds and two time-limit failures. The completed
specified-field cases tighten east allowances by about 3.4% and height by
about 10%. Completed [runtime profiles](ilvis0-transport-runtime-profile/INTERPRETATION.md)
locate major costs in repeated exact-arithmetic bound operations. The
[compiled implementation](ilvis0-compiled-transport-controls/INTERPRETATION.md)
now passes all 24 native controls and the [six-source long screen](ilvis0-compiled-range-preflight/INTERPRETATION.md).
Both earlier timeouts are resolved. The [physical source calculation](ilvis0-source-value-controls/INTERPRETATION.md)
now also passes all six complete-prefix checks. The
[rounded training adapter](ilvis0-rounded-source-controls/INTERPRETATION.md)
passes its six-source qualification too. The
[revised native trial](ilvis0-source-native-v2-controls/INTERPRETATION.md)
passes all 24 controls on the original calibration boxes and caps. Its
[long-source screen](ilvis0-source-range-preflight/INTERPRETATION.md) completes
two cases; four reach the time limit. Height allowances improve, but horizontal
ones widen. Runtime and horizontal Taylor bounds are next; the complete width
target remains open.

## Then: four larger tests

| Order | Question | What is needed |
|---|---|---|
| 1 | **Can the models predict unused measurements?** | Fit earlier observations and predict later ones. Height must agree too; a better horizontal fit alone is insufficient. |
| 2 | **Does the result repeat in a different archive?** | Prepare ESA survey data under its own selection and instrument assumptions. Its first selection found no qualifying intervals. Keep separate flights reserved for confirmation. |
| 3 | **How much independent evidence is there?** | Group overlapping recordings and related flights. Establish confidence without counting every stretch as an independent experiment. |
| 4 | **What rotation field does the data measure?** | Fit its size and direction freely. Only then assess whether the precision can distinguish solar from sidereal timing. |

## What is already done

- All 53 main comparisons passed their numerical stopping checks.
- The [raw-gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) compares
  observed trends with geographic predictions across all 53 stretches.
- Initial checks without gyroscopes leave all candidate models possible.
  Those checks are not complete reconstructions of flights without gyros.
- Long-record processing has passed software tests. Separate ESA flight groups
  are reserved for confirmation.

The earlier airborne archive has already informed development. Tests on it can
check prediction performance, but they cannot become an untouched independent
confirmation. That is the purpose of the reserved ESA flights.

[Roadmap and task status](ANALYSIS_ROADMAP.md) ·
[Method](METHODOLOGY.md) · [Completed studies](STUDIES.md) ·
[Rotation-field proposal](ROTATION_FIELD.md).

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

The last complete generated-data comparison meets its fixed width target in
**four of six groups** on a 7.2-second example. Both globe groups with the
specified background field still miss it. No new aircraft prediction fits
follow until every group passes.

The [faster source calculation](ilvis0-batched-range-preflight/INTERPRETATION.md)
finishes all six long-history cases within the original limits. Height error
allowances shrink by 17–37%, while horizontal ones remain too broad.

The next method keeps track of how calibration changes the source, rather than
losing that information in a broad interval. It passes
[ten mathematical checks](ilvis0-source-derivative-v2-controls/INTERPRETATION.md)
and [24 complete native controls](ilvis0-taylor-native-controls/INTERPRETATION.md).
Across 348 checked bounds, predictions and coefficient matrices are unchanged
and error allowances do not widen. Its
[long-history screen](ilvis0-taylor-range-preflight/INTERPRETATION.md) passes all
six cases, with 6–11% smaller horizontal allowances in the profiled-processing
cases. The [training-transfer check](ilvis0-complete-source-preflight/INTERPRETATION.md)
passes in all 48 calibration regions, and the
[joint prediction adapter](ilvis0-taylor-joint-controls/INTERPRETATION.md) passes
all six known-answer cases. The
[complete 48-region comparison](ilvis0-taylor-complete-prediction/README.md) is
running, with about 65–80 minutes expected on four numerical threads.

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

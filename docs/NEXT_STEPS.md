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

The [completed smaller-box test](ilvis0-coupled-subdivision/INTERPRETATION.md)
also leaves four of six groups passing. Its [endpoint audit](ilvis0-coupled-subdivision/ENDPOINT_DIAGNOSIS.md)
points to conservative propagation allowances as the next improvement to test.
The [six-bound diagnostic](ilvis0-training-remainder-diagnostic/INTERPRETATION.md)
finds that smaller domains barely improve height allowances. The
[direction-preserving method](ilvis0-directional-native-controls/INTERPRETATION.md)
passes its static and native controls, but the [prediction comparison](ilvis0-directional-prediction/INTERPRETATION.md)
did not improve the complete globe groups. It replaced a tighter training-derived
bound with a weaker physical-only bound. Next is to preserve the training
information while improving how the dynamic calculation carries direction.
The [six-source value preflight](ilvis0-source-norm-preflight/INTERPRETATION.md)
passes and narrows the relevant vertical intervals substantially. Matching its
reference coefficients and bounding propagation error are the next checks.

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

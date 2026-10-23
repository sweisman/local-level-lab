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

## Now: predict measurements left out of the fit

Fit the earlier part of a recording, then reconstruct the later track from its
IMU readings. Keep later GPS positions out of calibration and use them only to
measure the errors. Check height as well as the horizontal track.

The [revised protocol](PREDICTION_VALIDATION.md) has two immediate steps:

1. Check the complete fitting and prediction pipeline on known-answer examples.
2. Run a small archival pilot selected by route, IMU type and conservative flight
   group. Use fixed starts and splits; report every result and failure.

The [existing saved-data comparison](ilvis0-saved-prediction-comparison/INTERPRETATION.md)
shows about 2.4 m later horizontal error for the specified-field globe, versus
143–255 m for the alternatives, on one recording. The next test asks whether
that advantage repeats on other groups and survives the declared assumptions.

Formal bounds covering every allowed calibration are a separate research track.
They no longer block exploratory prediction comparisons. The current bounded
calculation will finish and be preserved, with no new expansion of its limits.

This change does not turn sensitivity ranges into confidence intervals or model
preferences into detections. Actual measurement-error assumptions and calibrated
statistical confidence still need testing. The 53-stretch findings are unchanged,
and reserved ESA confirmation groups remain protected.

[Prediction protocol](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

## Then: four larger tests

| Order | Question | What is needed |
|---|---|---|
| 1 | **Can the models predict unused measurements?** | Fit earlier observations and predict later ones. Height must agree too; a better horizontal fit alone is insufficient. |
| 2 | **Does the result repeat in a different archive?** | Qualify the [rate and motion treatment](ESA_MOTION.md), then freeze receiver-only selection. The first inventory has no eligible stretches. Keep confirmation flights reserved. |
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
[Method](METHODOLOGY.md) · [Completed studies](STUDIES.md) · [Reproducibility](REPRODUCIBILITY.md) ·
[Rotation-field proposal](ROTATION_FIELD.md).

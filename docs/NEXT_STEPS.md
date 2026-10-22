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

The stronger test is to fit an earlier part of a recording, then predict later
positions—including height—without using them to adjust the answer.

Short software checks pass. The [long-record test](ilvis0-long-staged-feasibility-v2/README.md)
has now finished all six generated cases. They contain the known answers,
but **none gives usefully narrow ranges**. The next numerical task is to improve
those bounds before attempting new predictions on unused aircraft observations.

Recent checks identified calibration cross-effects that the simplest linear
calculation omitted. [Correcting the remaining curvature](ilvis0-residual-source-curvature/INTERPRETATION.md)
reduces mismatch in twelve generated examples to 0.64 m and 3.28 m RMS in the
two processing cases. This is improved approximation, not a confidence interval.

The latest [check against the original noisy observations](ilvis0-truth-probes/INTERPRETATION.md)
accepts six of twelve candidate calibrations. Their later north predictions
span **13.33 m** and **5.90 m** in the two processing cases. These sampled
spreads are not bounds on all possible calibrations.

A separate [zero-reference fixture](ilvis0-ray-probes/INTERPRETATION.md)
admits **21.75 m** north separation despite earlier agreement within 1 m.
That fixture cannot meet its 20 m width target by improving arithmetic alone.
The two problems have different observations; their results cannot be transferred.

A short [native reconstruction comparison](ilvis0-path-native-controls/README.md)
passes all six generated cases and all 27 parameter directions. Full-trajectory
and clock treatment still need qualification, along with the receiver/IMU
error model. The width targets and earlier failures remain unchanged.

The [compiled packet calculation](ilvis0-compiled-path-packets/README.md)
passes ten local checks. A separately frozen native comparison checks longer
prefixes: all six cases pass across 64 packets and all 27 parameters in 57
seconds. Full-record bounds remain the next requirement.

New aircraft prediction fits have not started. The 53-stretch findings are
unchanged. [Completion requirements](ilvis0-long-staged-feasibility-v2/V01_GATES.md)
explain what must pass; the [study record](STUDIES.md) preserves earlier results.

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
[Method](METHODOLOGY.md) · [Completed studies](STUDIES.md) · [Reproducibility](REPRODUCIBILITY.md) ·
[Rotation-field proposal](ROTATION_FIELD.md).

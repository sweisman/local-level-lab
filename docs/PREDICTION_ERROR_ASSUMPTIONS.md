# What the prediction error ranges assume

The immediate [prediction protocol](PREDICTION_VALIDATION.md) tests unused
measurements after training-only calibration. Formal bounds covering every
allowed calibration remain a separate research track. They are no longer a
prerequisite for exploratory prediction comparisons. **Neither ranges across
several fitted starts nor the existing formal bounds are calibrated confidence
intervals for the aircraft recordings.** The sources of error below remain separate.

An **IMU (inertial measurement unit)** supplies the gyroscope and accelerometer
records used to reconstruct motion.

The [ESA saved-error check](esa-error-structure/INTERPRETATION.md) examines 22
completed forecasts. Preferred-model later errors have lag-one correlations
near 0.99, and first differences remain correlated. These describe combined
prediction errors, not raw receiver noise. They motivate testing receiver-plus-IMU
uncertainty with known-error controls; they supply neither a fitted noise law
nor calibrated confidence.

The [completed known-noise controls](esa-noisy-prediction/INTERPRETATION.md)
produce 24 numerical passes and zero physical accuracy passes. Later horizontal
RMS is 83.6–88.6 m against the unchanged 10 m limit. Each candidate predicts
its own generated truth. This is an error-model development result, with no
new Earth-model comparison or change to the original aircraft findings.

The [training-only logged-rate check](esa-training-rate-variation/README.md)
examines 239,864 earlier samples. Its gyro and accelerometer contrasts change
substantially with sample spacing. These measured variations include aircraft
motion, vibration and processing; they are not isolated sensor noise. A logged
point-rate statistic also cannot be transferred directly to independent
increment noise: the ESA linear-point conversion shares sample endpoints.

The [analytic error-budget example](esa-noisy-prediction/ERROR_BUDGET.md)
shows how the declared gyro noise alone can accumulate into tens of metres
over a 400-second forecast, even with a perfect initial state. This is a
checked constant-level approximation, not measured archive uncertainty or a
replacement for the completed noise test. Accuracy limits and failure labels stay fixed.

The [shared state-space component](integrated-noise-covariance/README.md)
now reproduces supplied linear Gaussian covariance and training-only
conditional future means/uncertainty in 54 source-bound software checks,
including stationary changing bias and shared query/endpoint noise.
The [native extension](native-noise-linearization/README.md) now passes 38
complete-history controls using the existing motion equations. A separate
receiver extension passes 15 checks for offsets, drift and persistent errors.
Their combined path passes twelve native checks. Fifteen further checks
include calibration uncertainty in a fixed-design linear prediction, retaining
all nuisance directions and withholding finite covariance for unidentifiable
forecasts. These components propagate declared error assumptions; they do not
estimate the actual archive error law. Native nonlinear calibration, active
parameter bounds and uncertainty from estimating the noise law remain open.

The separate [rate-point law](integrated-noise-covariance/POINT_PLAN.md) passes
15 checks. It preserves the shared sample in adjacent ESA intervals and uses
point-error variance rather than continuous-rate PSD. Its 21-state native
adapter and 33-state receiver combination now pass separate controls within
the [182-check qualification](native-noise-linearization/README.md). The earlier
incremental-data path is retained and checked. Calibration is fixed in these
native controls; active bounds and nonlinear fitted-prediction coverage remain open.

The [training-only native adapter](integrated-noise-covariance/training-adapter-qualification/README.md)
now passes 56 checks. It freezes weighting from earlier observations, preserves
covariance normalization and retains all calibration columns. It withholds an
unrestricted-calibration covariance when the local correction leaves the allowed
box. This checks the interface; noisy nonlinear prediction remains unqualified.

| Source | What is currently checked | What still needs establishing |
|---|---|---|
| Calibration | Keep one set of physical calibration parameters shared across the whole generated history. Preserve the full declared domain. | Whether that domain and its time behavior adequately describe a particular recording. |
| IMU noise and quantization | Preserve the recorded increments as inputs to the generated calculation. | Their contribution to prediction uncertainty; constant calibration bounds do not automatically cover random sensor errors. |
| Approximation | Bound the error introduced by simplifying the nonlinear calculation. Check complete coverage of the permitted domain. | Useful widths over complete recording lengths. A short-example success is insufficient. |
| Numerical arithmetic | Use exact rational checks and outward-rounded primitive operations in the qualified components. Preserve reference-transfer errors. | A whole-program floating-execution bound; sampled agreement does not prove one. |
| Receiver observations | Check supplied error assumptions without consulting future observations. | An adequate error distribution and temporal covariance for the real receiver stream. |
| Physical model | Preserve the candidate's stated motion, gravity and processing assumptions. | Whether predicted unused positions, including height, adequately match observations. This is the later prediction test. |

## Available receiver information

The [saved inventory](ilvis0-receiver-metadata/README.md) covers all 53 selected
recording files. Their inspection reports list GGA/RMC/VTG/ZDA sentences and no
GST/GBS error-statistics sentences. About 96.5% of receiver-stream bytes were not
parsed as NMEA text. Their contents remain unidentified. Neither their presence
nor a receiver type code establishes an independent covariance estimate.

This limits what the current metadata can justify. Software sensitivity tests
can continue under clearly declared error laws; exact proprietary device
identification is supporting work. Empirical uncertainty and physical adequacy
remain separate requirements before a scientific decision.

## The short generated example

The present complete-cover comparison predicts a position at 7.2 seconds from
six earlier generated observation epochs. It keeps 27 physical parameters and
78 enclosing coordinates. The extra coordinates represent shared error terms
and products; they are not additional independent instruments or observations.

Its training constraints allow **1 mm per observed coordinate**, plus a separate
**0.00001 m arithmetic allowance**. These are frozen software-test assumptions,
not measured receiver precision or survey-IMU specifications. The saved outputs
explicitly leave whole-program floating enclosure and observational coverage
unqualified. Neither allowance can be carried into an aircraft study merely
because the example retains its known truth.

The width target is also a software-development target: halve the earlier
complete range without changing the problem. It is not a significance level
or an absolute adequacy criterion for a flight.

## Shared observation uncertainty

### The eight-minute coordinate-box fixture

The longer generated fixture uses an explicit ±1-metre allowance per training
coordinate and software width targets of 20 m north, 20 m east and 50 m height.
Those are development settings, not verified aircraft measurement errors.

The [nonlinear ray audit](ilvis0-ray-probes/INTERPRETATION.md) finds twelve
calibrations that meet every earlier constraint in a zero-reference fixture.
Under zero upstream removal, their later north predictions span 21.75 m.
An interval covering them all cannot meet the 20 m width target. This shows
genuine numerical ambiguity under those coordinate-box assumptions, alongside
any additional overestimation from a bounding algorithm.

The completed long-record study uses different, perturbed training observations;
the ray result is not its outcome. A model with additional joint error structure
is also a different problem and needs its own justification. None of these
software settings establishes aircraft confidence or warrants tightening a
calibration bound simply to make the target pass.

The [original-observation probes](ilvis0-truth-probes/INTERPRETATION.md)
check that distinction directly. Six of twelve candidates satisfy the actual
five-epoch constraints, with sampled north spreads of 13.33 m and 5.90 m.
These do not exceed the 20 m target, but they are not outer ranges over the
whole parameter domain. They neither refute that original target nor qualify it.

The [full-history calculation](ilvis0-long-staged-feasibility-v2/README.md)
retains the known answers but produces no useful ranges. A
[saved calibration audit](ilvis0-calibration-box-audit-v2/README.md) narrows only
the initial vertical-position and clock intervals. Orientation and sensor
calibration stay broad in this coordinate enclosure; joint relationships between
parameters must be retained rather than treating narrower individual intervals
as the whole training information.
The [complete static coupling check](ilvis0-static-training-coupling/README.md)
passes but narrows its acceleration allowance by only 3.7–7.1%. The
[exact width audit](ilvis0-prediction-width-budget-v2/README.md) attributes
77–91% of total width to reconstruction allowances, rather than rounding.
The [revised full-history comparison](ilvis0-long-remainder-feasibility/README.md)
reduces those ranges but still meets none of the original width targets. Every
case retains the known answer; this does not make its bounds useful.

### Is a wide range genuine or an overestimate?

Two different calibrations can establish a minimum prediction width if both
satisfy **the same original training observations and all physical bounds**.
If their later positions differ by more than a width target, no valid range
covering both can meet that target. A linear approximation alone cannot establish
this: each candidate must pass the nonlinear motion calculation, with the same
clock, coordinate frame and processing assumptions. Numerical-error allowances
must also leave enough margin for the claimed separation.

Such a result would identify insufficient training information under the stated
assumptions, not poor instrument quality or support for an Earth model. A search
that finds no such pair proves neither uniqueness nor useful uncertainty. Keep
future observations out of the search; it explores possible predictions, not
which prediction happens to match withheld data. Any search needs a separate
finite freeze and must preserve unsuccessful candidates.

The shared [saved-pair audit](../analysis/lll/ilvis0_truth_probes.py) checks these
inequalities with exact arithmetic. It performs no trajectory search and does
not establish the supplied numerical-error bound or verify source provenance
by itself. Those remain separate requirements before a physical conclusion.

The [completed nonlinear search](ilvis0-nonlinear-witnesses/README.md) returns
the starting calibration in both directions for five cases. Its zero spreads
do not narrow uncertainty; the earlier accepted 13.33 m north spread remains
valid. Only one pair differs, by about 3.70 m north. No original width target
was refuted, and no useful outer range was established.

The subsequent [controlled-step trial](ilvis0-feasible-step-controls/INTERPRETATION.md)
does find accepted alternatives under the original perturbed observations.
Their later north predictions span **22.99–23.27 m in every one of the six cases**,
after subtracting the declared numerical guard. Thus the 20 m target cannot be
met by a range containing all these allowed calibrations. This is a statement
about the represented native calculation and supplied error assumptions, not
measured aircraft uncertainty. The whole-program numerical guard remains
unqualified. The [denser check](ilvis0-witness-density/README.md) now evaluates those fixed
calibrations at one-second spacing. Four cases exclude common observation intervals
for all three calibrations, while two still permit them. No added observations
were invented. This does not supply new outer ranges or an aircraft error law.

A saved local-sensitivity trace attributes the coupled alternatives chiefly to
initial sensor orientation and accelerometer offsets. The compared calibrations
differ by about 0.36° in one orientation coordinate and 0.0005 m/s² in horizontal
accelerometer offsets. These are allowed coordinate differences, not measured
errors of the aircraft instruments. Individual derivative terms cancel strongly;
they are a local diagnostic rather than an independent causal decomposition.

### Joint error laws

The [shared-scale calculation](ilvis0-shared-reference-scale/MATHEMATICS.md)
assumes a stated covariance shape and Gaussian errors. Its reference projection
must be fixed independently of those errors, with positive residual degrees of
freedom. All physical candidates use the same scale source. A poorly fitting
candidate cannot give itself a larger measurement-error budget.

The software controls establish results under these supplied assumptions. They
do not show that receiver errors are Gaussian, that their covariance is correct,
or that the same law applies to another instrument or archive. A mismatched
reference can make a conservative range wide; that is not proof of large
measurement noise.

Receiver error and accumulated IMU error are different contributions. An
aircraft prediction error model must include both, or justify why an omitted
contribution is negligible for its declared test. A receiver-only covariance
does not become a complete error model merely because its software tests pass.
This assessment can use observations and stated sensitivity assumptions; exact
proprietary device documentation is not a prerequisite.

The [accumulated inertial-error component](ilvis0-inertial-error-controls/INTERPRETATION.md)
passes 28 software checks against an independent continuous-time reference. It
preserves correlation between training and future observations under a supplied
linear Gaussian model. Its noise inputs have no hardware defaults, and its
constant-coupling approximation is not yet an adequate error law for a flight.
Noise settings, coupling matrices and reference projections must not use
withheld positions. Estimating them from noisy IMU inputs also introduces
dependence that must be accounted for before applying an independence-based
coverage calculation.

The [longer-study training interface](ilvis0-recording-training-interface/INTERPRETATION.md)
requires an explicit allowance for each observation coordinate. Its 15 focused
checks prevent the short example's 1 mm allowance from becoming a silent default.
Supplying an allowance remains an assumption that needs justification.

The [combined error operator](ilvis0-joint-error-operator/README.md) now passes
15 focused checks against the dense reference, including a prediction at
438 seconds. It keeps receiver and accumulated IMU error correlated across
the split without storing a whole-record covariance matrix. The supplied
constant-coupling linear error law still needs justification for aircraft use;
these software checks do not establish empirical coverage.

The [simultaneous-allowance component](ilvis0-gaussian-allowances/README.md)
connects supplied Gaussian variance and scale bounds to per-coordinate training
and future allowances. Its probability budget covers all declared coordinates
together, without requiring independence. All six small staged model/processing
cases pass; the real error law and the supplied variance bounds remain separate
requirements.

The [exact marginal-variance bounds](ilvis0-joint-variance-bounds/README.md)
include the declared clock interval and fixed receiver/inertial origins under
the linear law. Twelve checks pass, including all 147 later noise epochs.
That supplies checked variance arithmetic for this law; it does not qualify
the physical predictions at every epoch or establish the aircraft error law.

## Before claiming calibrated aircraft prediction uncertainty

Freeze the calibration domain, observation-error family, numerical treatment,
prediction horizon and adequacy criteria before examining withheld positions.
The revised exploratory comparisons report direct errors and sensitivity without
claiming calibrated coverage. A formal interval method must still demonstrate
useful bounds over the intended recording length before claiming its own qualification. Missing or
unsupported regions must remain unsupported, rather than disappear from the
reported range. Keep every covariance alternative required by the frozen plan.

The archival prediction tests will be retrospective development validation.
Independent confirmation and confidence for the complete two-stage model
decision require their own reserved data and dependence-aware calibration.

[Current diagnostic](NEXT_STEPS.md) · [Technical backlog](ANALYSIS_DETAILS.md) ·
[Training-only interface](ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md).

### Fixed training summaries

The [receiver-only comparison](ilvis0-receiver-distance/README.md) and [joint-noise sensitivity](ilvis0-joint-distance/README.md) keep the same saved trajectories. Adding independent positive noise lowers their noise-scaled separation; neither calculation estimates actual instrument noise or supplies an observed likelihood ratio.

The [joint projection operations](ilvis0-joint-projection-controls/README.md)
support fixed training averages and trends at long-record size. The
[summary-error controls](ilvis0-summary-error-controls/README.md) now pass four
declared noise cases. Twelve time-only summaries and 441 later coordinate errors
share one Gaussian failure budget, the original covariance identity and a fixed
integration origin. Signed weights preserve time correlations; clock uncertainty
is covered explicitly. These are software examples, not instrument-noise estimates.

The nonlinear row interface retains all 27 physical parameters and every supplied
enclosure coordinate: 51 in the original source layout, or all 78 when auxiliary
product coordinates are present. It bounds unknown propagation remainders with absolute
weights and includes coefficient-rounding error. Arithmetic checks do not prove
that the supplied native enclosures or observation law are adequate.
[Complete prediction qualification](ilvis0-joint-projection-controls/NEXT_PLAN.md)
and observational coverage remain open.

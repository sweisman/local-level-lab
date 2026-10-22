# What the prediction error ranges assume

The current development tests check whether the software can bound a prediction
while calibration is uncertain. **Those ranges are not yet confidence intervals
for the aircraft recordings.** Several different sources of error must remain
separate.

An **IMU (inertial measurement unit)** supplies the gyroscope and accelerometer
records used to reconstruct motion.

| Source | What is currently checked | What still needs establishing |
|---|---|---|
| Calibration | Keep one set of physical calibration parameters shared across the whole generated history. Preserve the full declared domain. | Whether that domain and its time behavior adequately describe a particular recording. |
| IMU noise and quantization | Preserve the recorded increments as inputs to the generated calculation. | Their contribution to prediction uncertainty; constant calibration bounds do not automatically cover random sensor errors. |
| Approximation | Bound the error introduced by simplifying the nonlinear calculation. Check complete coverage of the permitted domain. | Useful widths over complete recording lengths. A short-example success is insufficient. |
| Numerical arithmetic | Use exact rational checks and outward-rounded primitive operations in the qualified components. Preserve reference-transfer errors. | A whole-program floating-execution bound; sampled agreement does not prove one. |
| Receiver observations | Check supplied error assumptions without consulting future observations. | An adequate error distribution and temporal covariance for the real receiver stream. |
| Physical model | Preserve the candidate's stated motion, gravity and processing assumptions. | Whether predicted unused positions, including height, adequately match observations. This is the later prediction test. |

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

The active long-record study uses different, perturbed training observations;
the ray result is not its outcome. A model with additional joint error structure
is also a different problem and needs its own justification. None of these
software settings establishes aircraft confidence or warrants tightening a
calibration bound simply to make the target pass.

The [original-observation probes](ilvis0-truth-probes/INTERPRETATION.md)
check that distinction directly. Six of twelve candidates satisfy the actual
five-epoch constraints, with sampled north spreads of 13.33 m and 5.90 m.
These do not exceed the 20 m target, but they are not outer ranges over the
whole parameter domain. They neither refute that original target nor qualify it.

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

## Before applying the method to aircraft predictions

Freeze the calibration domain, observation-error family, numerical treatment,
prediction horizon and adequacy criteria before examining withheld positions.
Demonstrate useful bounds over the intended recording length. Missing or
unsupported regions must remain unsupported, rather than disappear from the
reported range. Keep every covariance alternative required by the frozen plan.

The archival prediction tests will be retrospective development validation.
Independent confirmation and confidence for the complete two-stage model
decision require their own reserved data and dependence-aware calibration.

[Current diagnostic](NEXT_STEPS.md) · [Technical backlog](ANALYSIS_DETAILS.md) ·
[Training-only interface](ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md).

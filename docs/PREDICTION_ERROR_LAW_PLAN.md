# Qualifying prediction uncertainty

The next question is whether uncertainty estimated before a withheld period
actually covers later receiver positions. A small receiver precision number or
a close fit to earlier positions does not answer it. Prediction error also
contains uncertain IMU calibration, changing gyro and accelerometer errors,
shared receiver errors, and error in the motion model.

This work uses the existing state-space covariance and training-only prediction
components. Their software checks establish that they propagate a *supplied*
error law. They do not establish the law for an aircraft recording. The
[source-bound software qualification](prediction-error-law-qualification/README.md)
passes twelve focused checks. The fixed-law likelihood helper scores only earlier residuals,
including dense independent calculations for shared error and a fitted linear mean.
It retains the full declared mean-design column
space and requires explicit parameter scales for its rank cutoff. It reports
a numerical minimum without calling that law identified or calibrated.
The fitted-mean forecast diagnostic retains calibration uncertainty and
abstains when a training-null calibration direction changes the forecast.
Nonlinear fitting, active bounds, adjustable-law estimation and later coverage
remain open.
One known-answer control has identical training likelihood under white and
persistent receiver errors, yet the predicted next-epoch standard deviations
differ by a factor of 7.09. This illustrates why a training score alone cannot
justify a narrow forecast interval; it says nothing about the archive's error
law. With an unknown fitted linear mean, the corresponding standard-deviation
ratio is 10.0; that single training epoch has no residual degree of freedom
with which to estimate the error law. The [receiver overlap study](ilvis0-receiver-overlap/recorded-study/README.md)
constrains receiver disagreement but cannot see error shared by both receivers.
The [training-only drift check](prediction-drift-control/README.md) rules out
one simple extrapolation as a general remedy for the preferred-model forecasts.

A new **linear known-answer component** independently draws gyro increments,
accelerometer increments, changing sensor biases, receiver offset, drift,
persistent error and white error from separate random streams. Its covariance
is built by a separate state-space implementation. Four deterministic software
checks pass: 20,000 generated histories match the declared short-history
covariance within the test's sampling tolerance, and a correctly supplied law
gives plausible 95% withheld-receiver coverage across 300 independent seeds
and ten future epochs per seed, including an earlier-fitted constant mean.
This is a software control of a simplified linearized motion error, not a
full aircraft prediction test, a fitted archive law or calibrated coverage.
Selection and coverage under an estimated law require a finite study;
the fixed-law check alone cannot establish them.

The [finite identification trial](prediction-known-answer-identification/RESULT.md)
now verifies 400 generated histories across two error laws and two sampling
cadences. An earlier-only rule chose one of three candidate laws in 166 cases,
abstained in 234 and chose the wrong law in five. With the true law supplied,
nominal 95% intervals covered 3,764 of 4,000 withheld receiver epochs.
All four training designs had local information rank three, showing that
nonzero rank alone does not make a short history decisive. The first frozen
allowance failed a result-schema gate after all charges; the corrected second
allowance is separately preserved and verified. These are simplified linear
software findings, not aircraft uncertainty calibration. Next, the full
known-answer aircraft prediction must include all physical candidates,
processing cases, clocks and calibration boundaries.
The first full-pipeline building block now regenerates later receiver reports
from a separate noise stream and verifies that their earlier prefix exactly
matches the receiver values used for training. A dual-target wrapper saves the
aircraft forecast and both fixed-law uncertainty diagnostics before generating
later truth, then scores physical position and future receiver reports
separately. Three focused wrapper checks pass. A twelve-case short native
matrix passes real training fits, both target-specific covariance extensions
and the saved-output ordering across three physical models, both processing
cases and two synthetic IMU error-input forms. Future receiver covariance
differs from physical-position covariance as intended. The subsequent
[source-bound 48-case integration study](prediction-aircraft-error-integration/RESULT.md)
passes every technical data-path check across the clock and calibration matrix.
None of its short fits converged or passed the physical prediction check; all
48 decisions abstain. An independently seeded, longer known-answer study and
uncertainty-coverage qualification remain open.
A training-only candidate-law comparator now checks that each fit used the
same measured receiver and IMU prefix, ranks complete Gaussian training
scores, and shows how much the fixed-law future scales differ. Four local
software checks pass. It never selects a law for a scientific decision and
abstains when a candidate fit is unqualified or calibration reaches a bound.
The next finite study must fit both candidate laws to **the same** longer
generated aircraft recording; the 48-case technical matrix generated a
different recording for each law and cannot be reused for that comparison.

That [paired aircraft study](prediction-paired-law/RESULT.md) is now complete.
All 12 two-minute recordings and 24 matched candidate fits verify; every fit
passes the declared numerical and physical prediction screens. The lower
training score matches the generating IMU error law in only 6 of 12 recordings,
with a largest training-score separation of just 0.000083 negative-log-likelihood
units. The largest fixed-parameter future scale ratio is only 1.0000023.
At the frozen 300 Hz cadence, the point-rate standard deviations were set to
the increment-law white amplitudes divided by the square root of the packet
interval. Point errors share interval endpoints, so short-lag correlations
differ, but their accumulated low-frequency noise is nearly the same. This
explains why receiver-position forecasts barely separate the candidates;
merely lengthening the same-cadence test is unlikely to identify the law.
Calibration reaches an active bound in all 12 comparisons. Fixed-parameter
95% marginal intervals contain 1,924 of 2,880 generated physical-position
coordinates and 2,242 of 2,880 future receiver coordinates. These are
descriptive counts, not calibrated coverage: the intervals omit uncertainty
from the fitted, bound-active calibration. Every scientific decision abstains.
The [saved ESA timing check](prediction-paired-law/SAMPLING.md) now verifies
239,863 earlier packet intervals from development recording 187. Their
point-to-increment accumulated white-noise variance ratio is 1.00000469.
Actual packet-timing variation in this interval does not separate the laws.
Independent evidence about high-frequency sensor error would be needed to
identify one. For the intended receiver forecast, carry both as an ambiguity.
Separately qualify
bound-aware nonlinear uncertainty and its coverage on independent generated
recordings. Do not apply a candidate law or coverage claim to recorded
aircraft on this evidence.
An [affine bound-aware control](bounded-calibration-prediction/README.md) now
passes nine local checks, including boundary calibration, a training-null
direction and an independent dense check of its flight-style adapter. It
provides a conservative marginal interval under a *supplied*
Gaussian law and parameter box. A seven-check software helper now unions
matched affine intervals from all supplied error laws. It retains the wider
interval when laws disagree and does not choose by training fit. Coverage
still requires one supplied law to be correct and calibration to lie in its
box. A paired-flight adapter saves both
law intervals and their union before later truth is opened, preserves active
calibration bounds, verifies that each interval uses its own declared target
and error operator, and abstains when a candidate fit fails. Eight focused
checks pass. Four short native two-fit controls also pass. The
[paired bound-family study](prediction-paired-bound-family/README.md) must test
the full condition matrix before any coverage qualification. Neither control
establishes nonlinear or observed coverage. The nonlinear flight model and its
actual error law remain outside the affine guarantee. An earlier
[24-case nonlinear technical release](bounded-calibration-prediction/NONLINEAR_RESULT.md)
completed with 24 technical passes, 23 numerical stopping passes and 24
withheld-position accuracy passes. Bounded intervals contained all tested
coordinates for both withheld targets, with broad median widths. This small
development sample does not calibrate nonlinear or observed-aircraft coverage.
The saved numerical failure remains preserved. A separate
[48-case independent-seed check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
passes every predeclared numerical and withheld-position gate on two new
noise draws per condition. All tested coordinates fall inside the broad
bounds. This is a method check, not calibrated 95% coverage or an
observed-aircraft threshold.
The [saved diagnosis](bounded-calibration-prediction/NONLINEAR_DIAGNOSIS.md)
locates the failed step at a packet boundary. The subsequent
[eight-point noisy timing probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md)
uses the exact reconstructed case: timing-only changes track the tangent on
both sides of that boundary. Its technical wrapper remains terminal after a
result-schema error, and its hash-checked point values are descriptive only.
The coupled calibration/timing direction is still unresolved; the original
23/24 stopping result is unchanged. Independent-seed interval coverage is a
separate gate.
The [saved ESA forecast-dependence check](esa-prediction-error-scale/CORRELATION.md)
audits all 22 completed development forecasts from one recording. Median
successive-error correlation remains about 0.9998 after removing linear drift;
median detrended correlation at about 60 seconds is about 0.35. These are combined
IMU/receiver prediction errors, not independent samples or a fitted error law.
For the specified-field globe, the later-to-earlier fitted-residual RMS ratio
is 97.9 north, 177.9 east and 83.8 height. A fixed scale taken from training
fit residuals would miss the forecast growth on this recording; these ratios
do not identify its physical cause or calibrate an uncertainty interval.
The [NASA saved-epoch check](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md)
also finds growth across four consecutive quarters of the withheld interval
for nine specified-field settings on three recordings. These are repeated
settings, not independent flights or a fitted error law.
The [subsequent equal-horizon transfer check](prediction-rolling-origin/INTERPRETATION.md)
uses two separate earlier-only fits on those same three recordings. Eight of
twelve repeated settings have qualified fits at both cuts, but their
later/earlier directional RMS ratios vary sharply by recording and direction.
That development result does not calibrate an uncertainty multiplier or
establish coverage on an independent flight.
The later [four-group NASA transfer check](prediction-group-transfer/RESULT.md)
scores second-cut forecasts for three groups and abstains on one. All three
scored forecasts meet a fixed descriptive error reference and physical screen,
but their final-quarter height RMS is 8.4–10.3 times their first-quarter RMS.
The quarter comparison uses saved scores and no new fit. It reinforces the
need for an error law that covers growth through the withheld period.

A separate five-check affine control now splits the future-error allowance
across **all coordinates in a withheld stretch** and unions the resulting
intervals across the two supplied IMU error laws. If one supplied Gaussian law
is correct and true calibration lies in its box, the linear calculation has a
conditional whole-stretch bound. It does not establish that the nonlinear
aircraft forecast or an observed flight has that coverage. This control is
outside the already frozen 24-recording paired-bound study; applying it to
aircraft requires a separately frozen method and generated qualification. A
four-check wrapper now connects that calculation to both earlier-only aircraft
forecast targets and verifies their operator binding before a law union. The
wrapper also passes a short native generated-aircraft fit for both targets,
with all later observations withheld. Its two-law union now binds the exact
future time grid, so equal-length forecasts for different epochs cannot be
combined. Twelve focused checks pass. This is software integration, not a
qualified aircraft coverage result.

The [paired bound-family result](prediction-paired-bound-family/RESULT.md)
verifies 24 generated recordings and 48 matched fits. Both saved target
interval unions contain all later coordinates in all 24 recordings. The
four-start technical interruption was completed under a separately qualified
allowance without rerunning sealed work. This small matrix qualifies the data
path, not 95% whole-recording coverage or an observed-aircraft error law.

The first [96-recording whole-period attempt](prediction-simultaneous-law-family/RESULT.md)
failed at package import on every worker, before any fit was charged. Its sealed
technical failures provide no coverage evidence. The worker-level regression
check covers the cause. A [fresh seeded cohort](prediction-simultaneous-law-family-v2/RESULT.md)
completed 96/96 tasks, including 12 originally unstarted tasks under a
separate qualified continuation. Both targets contained every later coordinate
on all 92 scored recordings. Four original tasks stopped at the eight-hour
deadline and remain failures. The exact one-sided 95% upper failure bound is
9.28%, so the predefined 5% gate failed. A new frozen technical approach must
first resolve the runtime limit and then qualify generated coverage; this
result cannot certify observed-aircraft prediction intervals.

## Order and gates

### What the available flight count can establish

The selected NASA stretches form 27 conservative flight groups, which are not
all proven independent. Seven ESA groups are reserved for confirmation and use
different instruments and processing. They cannot simply be pooled into one
common failure-rate population.

For perspective, if **all** flights were independent draws from one fixed
population and **none** failed, the exact one-sided 95% upper bound on that
population's failure rate would be `1 - 0.05**(1/n)`. It is **10.5% for 27**
flights and **34.8% for seven**. At least **59 independent zero-failure flights**
would be needed to put this bound below 5%. The current groups are fewer and
their independence is not assured. This arithmetic applies to a
distribution-free observed failure-rate claim; it does not replace a separately
validated physical error model or make the existing numerical preferences less
real. Independent ESA replication remains useful even when it cannot certify a
rare failure rate by count alone.

1. **Known-answer identification.** Generate independent IMU and receiver
   histories with known sensor error, changing bias, receiver white error,
   persistent receiver error and drift. Use separate random streams. Fit any
   adjustable error-law quantities from the earlier portion only. Check
   parameter recovery and the rank of the identifiable combinations. Report
   an abstention when different laws give indistinguishable earlier data but
   materially different later uncertainty. The generator and estimator must
   not share the implementation of their covariance calculation.
2. **Known-answer prediction.** Withhold both later physical truth and later
   receiver observations until forecasts and uncertainty bounds are saved.
   Cover both targets separately: physical position and a future receiver
   report. Test all three physical candidates, both upstream-processing cases,
   both clock conventions and interior/boundary calibration controls. Score
   empirical coverage, interval width, forecast error, numerical completion
   and abstention separately. A point forecast that is close to truth does not
   qualify its uncertainty bound.
3. **Frozen finite study.** Before drawing the qualification cases, record the
   exact generator, cases, random seeds, error-law family, estimation rule,
   train/withheld split, coverage target, allowed misses, source and environment
   hashes, starts, evaluation limits and thread allocation. Qualify task-level
   interruption recovery. Preserve every failed fit and charge. Select no
   limits or correction using withheld outcomes.
4. **Observed development check.** Only after the known-answer gate passes,
   estimate the law from earlier observations of the already designated
   development recordings. Compare standardized later errors, temporal
   dependence, physical height and horizontal adequacy, and stated coverage.
   Keep the 53-stretch model-preference study unchanged. If the observed error
   structure is inconsistent with the frozen law, report failure and revise
   the law in a separate development study.
5. **Independent confirmation.** Freeze the method and flight-group identities
   before any protected ESA confirmation outcome is inspected. Count
   overlapping instruments and adjacent stretches as one dependent flight
   group where appropriate. Calibrate the complete two-stage shape/field
   decision separately from prediction coverage.

## Full-aircraft qualification bridge

The next generated control can reuse the independent aircraft trajectory and
sensor generator (`lll.airquantumgrav_truth`,
`lll.airquantumgrav_observation_truth` and `lll.airquantumgrav_noisy_inputs`)
with the existing training-only fit and continuous forecast. The new
`lll.airquantumgrav_withheld_receiver` helper checks that a regenerated full
receiver stream has **exactly the earlier measurements already fitted**. The
study worker must save the forecast before it requests later physical truth or
receiver reports. Physical-position error and future-receiver-report error
must be scored as different targets.

The existing ESA generated-noise study tests only its declared clock and does
not estimate a law from training data. A separate adapter must cover both
clocks, all three physical models, both processing cases, interior and
boundary calibration, and multiple earlier-only law candidates. It must
retain every numerical failure and abstention. Before launching that study,
freeze the exact cases, seeds, starts, law grid, coverage bounds, evaluation
limits, source hashes, recovery test and thread allocation. Oracle-law
coverage is a software control; an estimated-law interval earns its own
coverage result only when the earlier-only rule makes a qualified choice.
The twelve-case short native matrix uses a generated 300 Hz ESA trajectory and
the header-elapsed clock. A separate 200 Hz generated path now produces exact
nominal 5 ms intervals; four local checks pass, including real native fits
routed through each clock. Those two clocks are numerically equivalent on this
exact-period control. A separate declared timestamp/integration-period
disturbance now keeps the same generated IMU increments and receiver reports
while changing only logged packet intervals; a matched native check produces
different saved forecasts under the two clocks. This is a local deterministic
software control, not a measured estimate of archive timing error.
The 300 Hz generator is never relabelled as 200 Hz.

The independent generated sensor source now exposes a second, labelled
calibration case with Z gyro gain and bias at the declared fit limits. It
preserves matched receiver observations and random noise draws against the
interior case. A short 200 Hz native fit reaches its forecast with later truth
withheld. Boundary-case uncertainty coverage has not been qualified.

This sequence does not require an exact proprietary IMU manual. It does
require explicit, checked assumptions about what the logged increments retain.
Passing synthetic controls establishes performance under their generated law;
passing observed development alone does not establish calibrated detection or
independent replication.

The current component checks run with
`/home/sweisman/venv/bin/python -m pytest -q analysis/tests/test_prediction_error_law.py`
from the repository root. They are development checks; a later finite study
must freeze and verify its own source and test evidence.

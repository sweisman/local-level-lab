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
On ESA development flight 187, the [carrier-phase satellite check](prediction-observed-development/ESA_CARRIER_SATELLITE_INFLUENCE_RESULT.md)
kept the fixed shape preference after each single-satellite omission in a
linearized calculation. A controlled range error that mimicked a position
or clock change left the residuals at zero. To qualify an aircraft error
law, account for that type of shared error separately from the disagreement
across satellites or receivers.
The [phase-error propagation check](prediction-observed-development/ESA_PHASE_ERROR_SCORE_RESULT.md)
now also tracks each raw range error across neighboring half-second steps.
Under the independent-epoch assumption, dropping the correlation induced
by differencing would overstate score uncertainty by a factor of 3.83.
Error aligned with the fixed score direction remains much more consequential.
The [matched raw receiver study](prediction-observed-development/ESA_PARALLEL_RAW_RECEIVER_RESULT.md)
finds a 1.77 mm RMS difference between the two alternate receivers over the
later 120 one-second phase changes. Individual AIR1 differences exceed 4 cm.
The receivers share an antenna. Their signed differences can test a relative
error pattern, while common position-like error still needs a separate bound.
Projecting both sets of raw differences into the AIR1 path shifts its fixed
comparison by +0.062 and −0.148 score units, against a 7.13-unit margin.
These measurements support receiver-specific sensitivity on the development
flight. Common errors and aircraft prediction coverage remain open.
[Relative score check](prediction-observed-development/ESA_RAW_RECEIVER_SCORE_RESULT.md)
The [separate Galileo replay](prediction-observed-development/ESA_GALILEO_PHASE_PATH_RESULT.md)
uses different satellites and final orbit and clock products. Both later
scores fall within 0.06 units of the GPS result. The antenna and earlier
position anchor remain shared. This checks another source of path error
and does not calibrate absolute receiver accuracy.
The [withheld accuracy replay](prediction-observed-development/ESA_RECEIVER_ACCURACY_REPLAY_RESULT.md)
found all 24 preferred forecasts within the original position limits
across twelve same-antenna receiver paths and two settings. The closest
limits could be reached with an additional disturbance of 2.25 m RMS for
a code-only path or 3.93 m RMS among the original and carrier paths.
The common disturbance size and independent-flight coverage remain open.
The [held-pair covariance check](prediction-observed-development/ESA_COMPONENT_SCALE_TRANSFER_RESULT.md)
tested transferring a scale across matched turn and steady windows. The
common multiplier did not improve the reference count. The separate
variance components met the optimizer's stopping rule in one of eight
folds. The [native-whitened replay](prediction-observed-development/ESA_WHITENED_SCALE_TRANSFER_RESULT.md)
verified the scores but left the stopping count unchanged. The
[full-range check](prediction-observed-development/ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md)
then rules out any common set of the three scales under the working
reference. The error shapes or mean path need further study before a
shared covariance can be justified on these observations.
The [axis and time check](prediction-observed-development/ESA_FORECAST_ERROR_LOCALIZATION_RESULT.md)
finds a sufficient excess on each axis of the hardest turn after allowing
both added terms. The largest lower bound is in east. A replacement law
needs to address more than a vertical error term.
The [motion-dependent innovation check](prediction-observed-development/ESA_MOTION_INNOVATION_SCALE_RESULT.md)
improves the total held-out log score and reduces the largest turn's
excess. It gives a much worse quiet-window error and leaves the
reference count at one of eight. This motion term alone does not
supply a qualified whole-flight error law.
The [earlier-only delay fit](prediction-observed-development/ESA_CARRIER_DELAY_FIT_RESULT.md)
tests a two-term atmospheric correction using the GPS carrier geometry.
It moves the later path by 0.29 m RMS, with a 0.45% improvement in later
carrier-range residual RMS. That constrains the effect of the fitted terms
on the saved scores and leaves the true shared error unmeasured.
On [four partially overlapping development forecasts](prediction-group-transfer/COMPANION_RECEIVER_RESULT.md),
changing the scoring receiver after an earlier offset adjustment changes
height RMS by at most 0.32 m. Both references leave metre-scale height errors
on those epochs. Unmeasured common receiver error and the unpaired forecast
tails remain open.
The 53-stretch NASA development table contains ten conservative flight groups
with three stretches, but **none has a time interval common to all three
recorders**. This is a metadata-only intersection of each group's UTC start
and end columns. The existing two-recorder gyro comparisons therefore cannot
be turned into a three-sensor variance decomposition for this selected cohort.
Even a future three-way overlap would need checks for shared processing,
mounting and timing before estimating individual sensor error.
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
The [saved runtime audit](prediction-simultaneous-law-family-v2/RUNTIME.md)
accounts for the original eight hours and the separate one-hour continuation.
The [fresh-cohort plan](prediction-simultaneous-law-family-v3/PLAN.md) fixed a
12-hour allowance before drawing new outcomes; no sealed recording was rerun.
Its source-bound software, recovery and frozen-worker preflight checks passed.
The original launch closed after four completed recordings and four interrupted
starts; a qualified finite continuation completed the 92 unfinished tasks.
The [saved-only audit](prediction-simultaneous-law-family-v3/RESULT.md)
verified all receipts and replayed both withheld-target scores. Ninety-five of
96 recordings passed both fits and covered every later coordinate of both
targets. One failed numerical stopping and counts as a failure. The exact
one-sided 95% upper failure bound is 4.85%, passing the frozen 5% gate for
this generated mixture. Observed-aircraft coverage remains untested.

## Next observed development check

If the new generated cohort passes its frozen coverage and technical gates,
use the already selected development recordings below to test whether its
declared uncertainty law describes real forecast errors. These recordings have
already informed method development; this step is an adequacy check, not
independent confirmation.

| Archive | Saved selection | Existing earlier/later split |
|---|---|---|
| NASA | `3df34ea39a6cbdbe15bb0f36` | First two-thirds of receiver epochs train; final third scores. |
| NASA | `7024120d59221e8eaf127084` | Same saved pilot split. |
| NASA | `0e73879f98c3b701fd7c42df` | Same saved pilot split. |
| ESA | Development recording 187 | First 800 receiver epochs train; final 400 score. |

The NASA identities and source hashes are in the [saved selection](ilvis0-prediction-pilot-preparation/selection.csv).
The [ESA execution record](esa-observed-wide-pilot/EXECUTION.md) fixes its
recording and split. First assess the **unchanged, fixed two-law union** as an
explicit assumption on these recordings. Its generated coverage does not
establish that either supplied law describes an actual IMU. A data-fitted law
or scale needs separate known-answer qualification and may use earlier data
only. Save forecasts and intervals before reading later receiver positions.
On generated controls, score physical position and future receiver reports
separately. On archival recordings the true physical path is unobserved:
score the withheld receiver report, and label any comparison with the ESA
GNSS-only PPP export as a receiver-based proxy, never direct physical-position
coverage. Report horizontal and height errors, whole-period receiver coverage,
interval width, temporal dependence, and every numerical or physical-adequacy
failure.
Repeated settings within one recording are sensitivities, not independent
flights. The seven reserved ESA confirmation groups remain closed.

Before any new fit, qualify the observed-data adapter and freeze exact inputs,
sources, environment, law candidates, starts, recovery procedure, finite
evaluation and wall limits, and four-thread allocation. If the generated gate
fails, preserve that result and diagnose it before this dependent check.
The generated recordings last two minutes; the ESA development interval has
about 360,000 IMU samples and 1,200 receiver epochs. A bounded, source-bound
preflight at that actual size was required to verify runtime, storage and the
earlier/later boundary before a full observed study could be launched. No
software pass on a short recording established that longer run's feasibility.
The structured operator
stores matrices per receiver epoch, so its declared 1,200-epoch storage is below
18 MB even at its maximum supported 40-state size; that bound does not cover
the rest of the fit or the work of processing 360,000 IMU samples.

Implementation order for the observed development check:

1. Add a shared observed-input adapter under `analysis/lll` that reuses the
   saved NASA and ESA selection/split materials. It must expose the full IMU
   history and earlier receiver rows to both fixed laws, while withholding
   later receiver rows until both interval artifacts are saved. Test changed
   hashes, split boundaries, law identities and an attempted early score read.
2. Run a separately bounded preflight at the ESA development recording's
   roughly 360,000-sample/1,200-epoch size. Check the 800/400 split, native
   call charge, peak storage, runtime and recovery before freezing any full
   observed fit allowance. This is a feasibility check, not a model result.
3. Freeze and run a finite pilot on the four already designated development
   recordings. Preserve all failed fits and score the withheld receiver
   intervals only after saving predictions. Physical-position intervals can be
   reported as assumptions but cannot receive a direct coverage score because
   the archive contains no known true aircraft path.

The [full-size preflight](prediction-observed-law-preflight/RESULT.md) has now
passed all four no-fit technical tasks under its separate finite allowance.
It used the prepared ESA development input with 360,028 IMU packets, 1,200
receiver epochs, 800 earlier epochs and a 239,867-packet training prefix.
Both supplied laws and both prediction targets constructed successfully in
about 27.5 minutes with four one-thread workers; each operator stored
6.7–10.0 MiB. The first frozen attempt failed at a source-key check before
native work and remains sealed. The corrected run preserves the later-receiver
boundary and supports the next [separately frozen observed development fit](prediction-observed-development/PLAN.md).
It does not test prediction coverage or establish which law describes the IMU.
The observed-fit adapter passed its source-bound and recovery controls. The
one-recording development forecast and follow-on checks have now closed.
The [600/200 result](prediction-observed-development/TRAINING_SPLIT_SCORE_RESULT.md)
initially covered all 200 later heights, but a [fixed-fit extension](prediction-observed-development/TRAINING_SPLIT_EXTENSION_RESULT.md)
shows the same calibration covers 0/100 heights in its last 100-report bin.
The earlier 800-report fit also covers 0/100 on that shared bin. The two
supplied IMU input-error laws give virtually identical results; choosing one
by its training score cannot fix this height-error failure. The current
observed-aircraft error law remains unqualified, and all seven reserved ESA
groups remain unopened.
The [training-only innovation replay](prediction-observed-development/TRAINING_INNOVATION_RESULT.md)
now reconstructs both covariance operators without later receiver values.
It finds persistent fitted height errors after whitening, nearly identical
under the two laws. This warns against treating the current laws as measured
aircraft uncertainty, but a formal rejection threshold still requires
generated full-fit calibration.
The [saved local-fit audit](prediction-observed-development/TRAINING_LINEAR_REFERENCE.md)
then checks all 26 fitted calibration directions. Both have full local rank
and reproduce a whitened cost near 7.15 across 1,800 training coordinates;
the linear known-covariance reference after fitting 26 directions is 1,774.
This large scale mismatch is a diagnostic, not a calibrated nonlinear test.
The [two-recording known-answer control](prediction-observed-development/FIT_ADJUSTED_CONTROL_RESULT.md)
completed four matched 600-report fits. Their training costs were about 1,781
and 1,815, compared with 7.148 on the ESA development recording. All four
generated fits passed numerical stopping but reached calibration bounds. The
control did not reproduce the tiny observed cost; two records do not calibrate
its lower-tail probability or establish the observed-aircraft error law. The
next gate is to explain the observed training/later-prediction mismatch before
freezing a larger calibration design.
The [saved boundary audit](prediction-observed-development/FIT_ADJUSTED_BOUNDARY_REPORT.md)
finds that releasing all active limits reduces local linear cost by only
1.477 or 3.647, far short of the generated-versus-observed gap. This does not
rule out a different nonlinear solution. Observation-model adequacy and the
observed training/later-prediction mismatch remain the next gates.
The [saved residual comparison](prediction-observed-development/FIT_ADJUSTED_RESIDUAL_REPORT.md)
finds generated fitted errors near unit whitened RMS on every axis, while the
ESA development fit has RMS 0.063 and a persistent height component. This
narrows the diagnostic mismatch but does not identify a physical cause or
calibrate a fitted-error distribution.
The [saved rate-variation comparison](prediction-observed-development/GENERATED_RATE_COMPARISON.md)
finds far larger short-span changes in recorded ESA body-axis rates than in
either generated input, even though the ESA fitted training error is much
smaller. Aircraft motion, vibration and processing are mixed in, so these
contrasts cannot be substituted for an isolated IMU-noise estimate.
The [saved known-answer forecast score](prediction-observed-development/FIT_ADJUSTED_FORECAST_REPORT.md)
finds 50–84 m future horizontal RMS error across the two generated records,
despite four numerically passing fits and training costs near the declared
scale. This is a software-control failure of prediction under the chosen
stress settings. Diagnose fit, calibration and motion contributions before
using those controls to qualify an observed-aircraft error law.
The [separate known-calibration control](prediction-observed-development/ORACLE_NOISY_REPORT.md)
has now completed two hash-checked forecasts on those same noisy streams.
Known calibration leaves 59.66 m and 637.12 m future horizontal RMS; fitted
calibration gave 50.47 m and 84.35 m. Calibration recovery alone cannot
explain this failure. The
[matched long clean control](prediction-observed-development/ORACLE_CLEAN_REPORT.md)
has since completed with 0.035 m horizontal and 0.322 m vertical future RMS.
The large noisy-stream drift appears after IMU error injection in this
software setup. The controlled error-component results below do not establish
the recorded aircraft's error law.
The [matched channel controls](prediction-observed-development/ORACLE_CHANNEL_REPORT.md)
show that the injected gyro stream dominates horizontal drift on both saved
draws. This is a channel attribution for those draws, not an estimate of the
archive's gyro noise or a separation of white error from changing bias.
The [four frozen component forecasts](prediction-observed-development/ORACLE_GYRO_COMPONENT_REPORT.md)
now separate those two injected gyro components on the same generated draws.
Both can drive large horizontal errors; in one draw their effects partly
cancel. This identifies a source of generated forecast error but does not
estimate the recorded aircraft's error law. Existing [saved-rate](esa-training-rate-variation/README.md),
[cross-channel](prediction-observed-development/RECORDED_CHANNEL_DEPENDENCE.md)
and fitted-residual diagnostics already show strong short-time and temporal
structure. The
next gate is to qualify a prediction-error range that covers aircraft motion,
sensor error and receiver error together, followed by separately qualified
uncertainty coverage.
The [analytic control](prediction-observed-development/ERROR_ATTRIBUTION_CONTROL.md)
shows that sampled IMU and one-second receiver reports can remain identical
when real platform vibration is exchanged for correlated sensor error.
Intrinsic sensor noise therefore needs independent motion constraints; an
effective whole-pipeline error envelope is the alternative target.
The [matched long error-scale calculation](prediction-observed-development/ORACLE_MATCHED_SCALE_REPORT.md)
now confirms that the two synthetic laws imply nearly identical expected
future RMS scales on the same 900-second trajectory. Their two saved
realizations differ greatly. This checks the covariance calculation on the
correct horizon but cannot establish coverage from two draws.

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

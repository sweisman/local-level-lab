# What still needs validation?

An **IMU (inertial measurement unit)** measures turning and acceleration. This experiment aims
to use its slow turning measurements during level flight to distinguish a rotating globe,
a stationary globe and a stationary flat disc. Different predictions alone are not enough:
the actual recordings must separate them despite IMU errors and aircraft motion.

The app and analysis tools are implemented. The project is still developing and checking the
scientific method. Successful software tests and simulated recordings do not establish that
a real IMU can deliver the required measurements or that the final decisions are reliable.

## What has been checked?

The software can decode recordings, retain interruptions and instrument settings, guide
calibration and compare measurements with model predictions. Automated checks cover the model
calculations, timing, uncertainty calculations, recording integrity and analysis rules.

Two development campaigns of 1,000 simulated flights each are complete. The first included
one accepted case that wrongly rejected its generating model under the provisional rule.
The second included none among its accepted cases. Their settings differ, and these findings
cannot be combined into a claim about a final error rate. The runs helped identify problems
and choose further tests; they were not independent validation of a finished method.

The experimental analysis now reports globe versus the specified disc separately from the
rotation question. Applying that rule to the preserved pairwise decisions gives 889 correct
shape preferences in the first pilot and 900 in the second, with no incorrect preferences and
111 and 100 abstentions. These include 9 and 12 preferences where the three-model decision
abstained. No flight was rerun. The historical simulation settings differ from the current
airline-route studies, and this combined decision has no validated error rate.

Fixed route-direction controls also show why the shape question deserves separate attention:
an assumed eastbound traversal of the longer route preserves both globe/disc contrasts under
one wind description while leaving rotation unresolved. It still fails under the broader
wind description. The control is a reversed assumed path, not an observed return flight,
and does not establish an accepted protocol. See the [direction review](research-next-stage-20261006/DIRECTION_REVIEW.md).

A subsequent coarse search checked 176 overlapping two-hour windows across all seven
recorded tracks, without requiring an earlier 75-minute window to pass. Seven combinations
of window and fixed IMU-turn pattern passed the preliminary motion, duration and heading
checks. None passed any model contrast under the nominal wind calculations. On this grid,
no eastbound window passed the heading requirement. This narrows the observed-route search;
it does not rule out other timings, durations or routes, and adds no simulated flights or
validated decisions.

The following three-/four-hour check added 277 windows and ten preliminary passing
window/turn combinations, again with no nominal model-contrast pass. Of these, 250 windows
failed supported position coverage. No four-hour combination passed preliminary geometry.
The [longer-route review](research-next-stage-20261006/EXTENDED_ROUTE_REVIEW.md) explains
the fixed timings and search limits. Longer duration alone has not established a useful
protocol in these recorded-route controls.

Varying safe turn timing subsequently produced candidate-specific partial design passes:
88 schedules across 11 windows gave 16 nominal schedule/pair passes under the physical
wind/airspeed candidate alone. None passed any pair across both wind candidates. Bounded
registered-state sensitivity checks disproved five nominal passes; eleven remain unresolved
after the small check. These are design clues, not calibrated pairwise decisions. See the
[turn-timing review](research-next-stage-20261006/TURN_TIMING_REVIEW.md).

The strongest stationary-globe/disc control has since passed the complete registered
physical-wind envelope: 15,210 states checked in 29.70 seconds, with worst direct-pair
retention0.365100 against0.312250. Its rotation comparison passes narrowly in the direct-pair
calculation, but fails after the global rank cutoff; rotating globe versus disc still fails.
All states have global rank1. This is finite-grid design evidence under one wind model,
with assumed interpolated motion and supplied axes. Full simulated-IMU preprocessing,
recovered axes, justified wind assumptions and independent calibration/validation remain
necessary. No new simulated flight or empirical decision was produced.

The separately authorized six-case full-pipeline replay has now completed: three truths,
two wind candidates and combined wind/IMU drift on the fixed Chicago–Los Angeles control.
All six fits converged and retained 99 cruise minutes with adequate headings. Both wind
candidates passed the stationary-globe/disc and rotation pairwise gates in every case;
rotating globe versus disc failed throughout. All decisions abstained because this pilot
used zero bootstrap and no calibrated thresholds. Residual-based gyro variation was about
38.3°/hour, substantially above the planning grid's3–6°/hour. Profile uncertainty remains
large, so this is processing/partial-geometry evidence, not a validated separation or power
claim. The [replay summary](observed-pair-replay-20261007/SUMMARY.md) records the outcomes.

A subsequent saved-data audit traced the large variation mainly to motion correction.
Changing aircraft acceleration changes the accelerometer's apparent vertical direction;
the current analysis treats that change as IMU tilt. The resulting false correction is about
38°/hour in this replay, while the simulated sensor/calibration remainder is about4°/hour.
Substituting the simulator's true gravity direction lowers the residual to about12°/hour,
but that direction is unavailable on an actual flight. This diagnoses a processing limitation;
it does not repair the pipeline or establish power. A correction using observed position and
IMU data, with acceleration and orientation uncertainty carried through, is needed.

An observed-data research prototype has now been checked on those saved observations.
On the same85supported minutes, replacing motion correction lowers variation from about
34to11°/hour with the saved model parameters held fixed. It preserves83minutes under all
93registered sensitivity states, with no failed states. Wind/orientation sensitivity can
still raise variation toward37°/hour. Eleven focused physical, gap and uncertainty checks
pass. This is a processing prototype with provisional uncertainty propagation; production
and calibrated decisions remain unchanged. The
[acceleration-correction study](acceleration-motion-20261007/README.md) records the scope.

The subsequent joint research fit recomputes motion correction and model orientation together
as wind, forward direction and six explicit measurement-error parameters change. All24fits
across the six saved cases converged, with correctly nested free/fixed objectives and no
parameter-boundary flags. Each uses the same83minutes; residual variation is7.92–8.57°/hour.
Sixteen focused checks and checkpoint/resume verification pass. These are development refits
with the original weights and a provisional error model, without bootstrap or calibrated
decisions. The [joint-fit study](joint-acceleration-motion-20261007/README.md) records the
results. A saved-data bandwidth check now applies identical additional filtering to
observations and complete reconstructed predictions. On the same79minutes, residual
variation falls about9–10%, from7.85–8.32to7.08–7.48°/hour. This is a diagnostic with
fixed fitted parameters, not another fit. The propagated gyro-only covariance includes
filter overlap and cross-axis correlations, but assumes independent one-second errors.
Fitted residuals show appreciable time correlation; full GPS/accelerometer/gyro error
propagation and the effect of nuisance fitting remain open. Twenty-one focused checks
pass. The [filtering study](matched-measurement-motion-20261007/README.md) records the
scope and limitations; no scientific decision or production change follows.

The subsequent [shared-error study](continuous-measurement-motion-20261007/README.md)
evaluates every prediction term at GPS timestamps. All six saved cases retain79minutes
and7.08–7.48°/hour of residual variation. Shared GPS/IMU propagation predicts about11.3°/hour
under provisional independent-second assumptions, with about90% of variance from GPS.
Local fit response includes shared GPS errors in the wind constraint. This is not a new
fit or validated uncertainty. Twenty-nine focused tests and independent derivative,
covariance and least-squares checks pass. Time correlations and mount/calibration/
instrument uncertainty remain open; no decision or production change follows.

The [time-correlation sensitivity study](temporal-measurement-covariance-20261007/README.md)
now evaluates36fixed combinations of GPS/IMU persistence per saved case,216scenarios total.
Marginal scales and79-minute support stay fixed. Predicted variation spans11.25–42.31°/hour;
local fit-response variation spans11.13–40.65°/hour. These assumed input-error processes
are not measurements of device behavior or calibrated bounds. All combinations remain
recorded;34focused tests and independent covariance/response checks pass. Next verify a
research objective using full shared-input covariance before separately scoping refits.

That [research objective](covariance-measurement-objective-20261007/README.md) is now
implemented and checked across all216saved-state scenarios. Joint whitening retains
gyro/wind cross covariance; matrices stay fixed during coefficient changes. Gaussian
normalization is reported separately; singular covariances fail explicitly. A second
216-scenario comparison retains the physical wind candidate's existing2m/s model
discrepancy as explicit covariance, alongside measurement errors. Broad wind is unchanged.
All44focused tests and independent objective/response checks pass. No new fit, calibrated
decision or production change ran in that study. The next
[saved-recording comparison](covariance-refits-20261007/README.md) is now authorized
and complete: six saved cases from three simulated recordings, four fixed assumptions
about how long GPS and IMU errors persist, and four fits per comparison. All 96 fits
converged and all 24 comparisons nested correctly, with no repairs, failures or
parameters near their bounds. Residual variation ranges from 4.47 to 9.88°/hour.
The injected model remains the best fixed fit across the assumptions, but comparison
strength changes sharply. Local rotating-globe/disc information retains only 4–14%
after nuisance projection. Other pairs retain more, including the stationary-globe/disc
comparison. These fitted-state diagnostics do not replace the design gate or establish
significance. No new flights, bootstrap or calibrated decisions were produced.
Actual GPS and IMU error persistence, reference and calibration uncertainty still
need measurement before choosing a defensible covariance domain and validating decisions.

The next [measurement diagnostic](INPUT_PERSISTENCE.md) is ready for explicit still
recordings. Nine controlled tests verify second coverage, saturation/gap handling,
cross-channel covariance, lag/block arithmetic and missing GPS/longitude-wrap behavior.
It retains mean-only and detrended views; it selects no noise model or scientific
threshold. No real measurement has run, and no new simulation campaign is included.

Later work asked whether the flight route and IMU-turn schedule actually leave enough
separating information. A 300-case study found no geometry that passed every required comparison
under both ways of allowing for wind. The subsequent audit found a numerical dependence on
parameter units and corrected it. It also found that short legs can lose their qualifying
cruise, slowly changing IMU errors can absorb model signals, and protective mount checks can
remove otherwise useful data.

A fresh 72-case comparison finished in about nine minutes. Every case returned a fit, but
neither the original schedule nor a proposed 90-minute schedule passed all comparisons.
The original schedule worked consistently under one description of wind-related uncertainty,
while the other description remained unreliable. The longer schedule failed its required
separation checks despite looking promising in a simplified calculation. One planned IMU turn
also overlapped an aircraft turn. Independent motion examples show that such an overlap can
corrupt the recovered IMU orientation, but its contribution to the campaign failures remains
unisolated. Saved diagnostics show separate losses to allowed measurement effects and the
numerical cutoff; moving the turns alone is not an established solution.

This leaves experimental design and reconstructed orientation as immediate research questions.
A longer flight or a more elaborate correction cannot be assumed to improve the result.
See [Evidence so far](EVIDENCE.md) for a readable account of the completed work.

## What must happen before strong claims are made?

First, the project needs a practical route and IMU-turn procedure that remains informative
after the full recording and analysis process. All required model comparisons must survive
the allowed IMU and aircraft uncertainties, rather than only the simplest calculation.
The [processing review](protocol-development-20261006/PROCESSING_REVIEW.md) identifies a timing
correction to test. Aircraft-motion checks during deliberate IMU turns are now implemented;
a new campaign must assess their effect on useful data and orientation errors.

An experimental wind correction now uses a slowly changing wind vector and speed through
the air, constrained to agree with GPS ground motion. Controlled checks cover its fitting,
uncertainty calculations and refusal to decide near its parameter limits. These checks do
not yet show that it preserves the Earth-model differences better than the earlier correction.
A comparison using the same simulated recordings for both corrections is needed next.

An optional magnetic-ambiguity comparison is also implemented. It retains most flagged data
while allowing possible IMU mount movement, and checks the result against the original exclusion
method. Both must be informative and agree. Controlled examples test this refusal to decide
when the methods conflict; a flight campaign has not yet established how much useful evidence
it preserves. It cannot apply a final empirical decision policy.

The software now checks whether a recording falls inside the flight conditions declared for
its decision thresholds. The range covers route geometry, ground speed, usable duration,
data gaps and IMU-turn timing. Missing information or conditions outside that range cause
abstention. Simulated and recorded GPS have separate identities. This guard is implemented;
choosing and independently validating a useful range remains unfinished.

Real IMUs must pass the [bench tests](BENCH.md). These include preserving a separately imposed
slow rotation, repeatability on different days, drift, temperature and Bluetooth behavior.
The current project work has no completed real-IMU validation evidence.

Then the final analysis and its acceptance rules must be fixed in advance, including the
software and numerical environment. Fresh simulations will set the decision thresholds.
A separate, previously unused campaign must test those thresholds and measure wrong decisions.
If the method is changed after those results are examined, another independent check is needed.

The intended wrong-rejection limit is roughly three cases in a thousand. Demonstrating such
a small rate needs far more evidence than a few hundred accepted simulations. Earlier restricted
plans required hundreds of thousands of simulated attempts in total; those cost estimates must
be refreshed after changes to the method and its usable flight domain. The full campaign has
not run, and no final empirical decision thresholds have been established.

A resumable runner can now split that work between two processes while preserving the fixed
experiment and every failed attempt. It protects against duplicate results and incomplete
campaigns being mistaken for validation. Large-run speed and storage still need measurement.

## External flight tracks and missing GNSS

The app can keep recording the IMU when phone GPS is unavailable. Airline, flight number,
scheduled origin-local departure date and route help locate a public track afterwards.
This preserves useful collection options but does not yet provide a validated GPS replacement.

Before an external track can support analysis, its flight identity, recording overlap, clock
alignment and position uncertainty must be checked. Coarse samples can miss turns; estimated
positions and long gaps cannot be treated as measured fixes. Reported altitude also needs a
known reference or explicit uncertainty. The original recording remains unchanged and the
external track remains a separate source with its own terms.

Seven public or supplied position tracks have been reviewed for development. Five have prepared
windows; two remain blocked by coverage. Replaying their geometry with simulated IMU behavior
is implemented and checked with controlled examples. Three matched evaluations on the assumed
Frankfurt–Johannesburg path failed before fitting because IMU roll and GPS-derived bank did
not provide a usable forward reference. The failures are preserved; no model comparison was
obtained, and a larger replay has not run.
Saved-data checks traced numerical problems to amplified GPS course noise and artificial
bank changes between public positions. Matched smoothing improves agreement in a diagnostic;
an explicit smoother assumed path removes bank steps.
An opt-in method now estimates angle uncertainty from the joint GPS/IMU relationship with
correlation and gap handling. Controlled tests include frequent small aircraft corrections;
a fresh smoother-route replay has now completed three full-pipeline evaluations without analysis
failures. All fits converged, but all abstained: only 57 minutes of usable cruise survived,
heading diversity was insufficient, and none of the intended model contrasts passed the
design-identifiability requirement. There were no magnetic movement flags; the optional mount
comparison could not establish agreement because both paths lacked identifiable contrasts.
These matched evaluations share one generating condition. They do not validate uncertainty
coverage, decision thresholds or false-rejection rates. The approved three-case budget is spent;
the other 15 proposed cases remain unrun. Historical outcomes remain unchanged.

Further geometry-only checks screened 192 overlapping 75-minute windows in the saved tracks.
None passed the motion, duration and heading screen with safe IMU turns; one lacked reported
height for evaluation. Longer extensions produced a more promising 120-minute Abu Dhabi–Chicago
candidate with turns at minutes 25, 50 and 85. Its approved initial three complete analyses
converged without failures and retained 97 cruise minutes with sufficient heading diversity.
All nevertheless abstained because every intended design contrast failed identifiability.
The estimated forward-direction uncertainty was 2.19°; coverage is unvalidated. No magnetic
movement was flagged, and the mount comparison was unavailable because neither path had
identifiable contrasts. The budget is spent and 15 proposed cases remain unrun. These
development selections change neither acceptance rules nor historical results and supply
no independent validation. The two pilots used different seeds and routes.

Saved-array diagnosis finds the allowed smooth bias drift dominates most model-information
losses, including at nominal conditions. Removing wind alone or tightening forward-angle
uncertainty does not resolve them. Westward motion also partly cancels the rotating globe's
horizontal prediction in this window; a nearly constant vertical difference can resemble bias.
Six nominal turn-pattern controls found one safe, more frequent pattern that improves separation
but still fails. An analytic design-tool bug that propagated missing courses into later valid
data was fixed; completed full-pipeline results are unchanged. These diagnostic omissions and
turn controls do not change the nuisance model, acceptance rules or collection protocol.
The sparse-fix replay preserves the original observations. A second replay explicitly assumes
a path between nearby fixes and simulates frequent GPS; neither supplies real IMU evidence
or enables operational use of an external track.

## Combining flights and partial evidence

A flight may separate two models while being unable to separate another pair. Experimental
code preserves that distinction and can abstain where information is missing. Combining such
comparisons needs its own decision rules and validation. Repeated use of the same physical
IMU must not be counted as independent instruments.

The newer experimental comparison fits each model pair directly, so usefulness for that pair
does not depend on a numerical choice about the complete three-model fit. It has its own
convergence, uncertainty and calibration rules. It cannot reuse thresholds for the older
comparison or supply a validated winner without fresh calibration and independent checking.

## Detailed research record

The [technical validation record](VALIDATION_TECHNICAL.md) preserves exact policies, historical
results, statistical plans and reproducibility details. [Research-record eligibility](PRIMARY_CORPUS.md)
explains which recordings can enter the provisional main result. Current confidence statements
remain provisional until instrument and independent statistical validation are complete.

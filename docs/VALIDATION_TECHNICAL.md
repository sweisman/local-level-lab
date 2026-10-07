# Software 0.6.0 validation and publication boundary

The correctness release preserves the physical model, provenance architecture, raw schemas 2/3
and WMM sensitivity check. Dynamic crab, noise weighting, bootstrap dependence, forward-axis
uncertainty and pooled significance remain research questions. Real slow-rate bench evidence and
demonstrated false-rejection tails remain publication blockers after these software corrections.

## Core-pipeline follow-up, 2026-10-06

[Implementation and prospective inputs](core-pipeline-20261006/README.md) supersede earlier
statements that trajectory integration, turn safeguards and diagnostic capture are pending.
Historical campaign outcomes are unchanged. The initial three matched actual-route development
evaluations subsequently failed before fitting, as recorded below. No optimizer search,
fresh calibration or independent validation has run, and no further campaign allowance exists.

### Initial airline-route replay outcome

The [fresh airline pilot](airline-pilot-preparation-20261006/README.md) spent its approved
three-attempt prefix on rotating-globe truth, wind plus mixed bias, seed 600900, simulated
frequent GPS on LH572 FRA–JNB. Wind/exclude, wind-TAS/exclude and wind-TAS/model-and-compare
all failed before fitting. Saved-data reconstruction reproduced identical forward regression
gain 0.0487347, R² 0.0122685 and bank energy 0.657473; the existing gain/R² minimums are
0.1/0.05. No orientation epoch was unresolved and 57 bins remained. The forward estimator
reported `roll/bank correlation too weak`; this is not an absent-turn classification.

The first error required positive measured forward uncertainty; the latter two required a
three-axis forward reference. No science fit, nuisance-envelope score, profile statistic or
winner was obtained. Per-attempt times were 8.1355/8.2483/6.3878 seconds, summing to 22.7715
known attempt-seconds; they cannot estimate successful-fit cost. Saved run files occupied
14,958,617 bytes at completion. The sharded export is partial, with three preserved failures
and 15 unrun cases; its status is `budget_complete`. No attempts remain authorized.

`analysis/tests/audit_airline_pilot.py` independently reconstructs the saved preprocessing
inputs without synthesis, science fitting, SVDs or search and writes `processing-review.json`.
Do not substitute simulator orientation, relax the reference gate or retry the failed tasks.
Review replay bank/roll and GNSS-proxy compatibility before another budgeted trial; public
interpolation does not establish the behavior of an actual flight with measured IMU data.

Subsequent saved-data analysis separates predictor noise from assumed-path roughness. The
scalar roll diagnostic explains 0.0122842 of variation with saved GPS versus 0.278223 with
noise-free assumed GPS. Position PCHIP has C1 continuity, but acceleration and coordinated
bank can jump: 137 interior knots, 11 bank jumps above 1°, maximum 15.9084°. Knot neighborhoods
contain 92.6293% of the sampled scalar roll energy. At 20 Hz, the full latent geometry's
scalar roll extrema are −162.189/+23.508°/s. These are interpolation artifacts, not empirical
aircraft-turn measurements.

Research-only matching of a centered 30-second Hann filter on the GPS bank-rate proxy and
horizontal gyro gives gain 0.925229 and R² 0.897332 over 4,187 fully supported windows.
Filtering splits at GPS/gyro gaps and rejects windows spanning missing observations. Existing
gain/R² minima remain 0.1/0.05; no angular uncertainty, primary gate, science fit or empirical
decision is supplied. The 30-second filter is development evidence; its error-in-predictor and
correlated residual uncertainty remain unresolved before integration. No smoothing sweep or
new flights were run.

`trajectory.smooth_track_spec` declares `observed-trajectory-replay-2`, selecting an explicit
natural C2 cubic per observed support block. Legacy version 1 remains PCHIP; version/model
mismatches are rejected. Position/height knots and support gaps are preserved. The prepared
FRA–JNB alternative hash is `5e69715fb544fd45612318a48f15136f7df97354289ecfdbc939e7dc16229d83`.
Its 20 Hz scalar roll extrema are −0.186935/+0.330154°/s; a finite one-sided knot check is
below 0.000307888°. Cubic overshoot and natural endpoint curvature remain latent-path assumptions;
these metrics do not validate real trajectory reconstruction or model separation.

Focused checks passed 51 tests in 2.39s, including independent rotation fixtures, noise-only
negative controls, missing-data support, cubic continuity, legacy compatibility and existing
core/preparation/audit checks. Current scientific source is now
`3b42547d5a2ffa2a2ef5d975382b4b1b2b0a762fe831493d40cb1b7f469cb682`.
The completed pilot retains its original `d5d63a6...` freeze; all prospective execution plans
must be refreshed after this source change. Additional attempt allowance remains zero.

### Opt-in matched forward-reference uncertainty

`forward_reference.py` implements `matched-forward-1`: common 30s Hann filtering, 5s course
differences, run-separated 60s Bartlett HAC, four complete covariance-duration windows and
frequent GPS (median interval at most 2s). Existing energy/gain/R² minima remain
`1e-4 / 0.1 / 0.05`. Direction comes from the normalized GPS/IMU cross-moment; its joint score
covariance uses observed predictor and response variation. For the angular tangent the
normalization's parallel component drops out. This assumes independent-error direction and
does not correct correlated-error or model bias. Gap boundaries sever covariance pairs;
duration-window counts do not guarantee statistically independent maneuvers.

Analyzer dispatch and measured sigma/tangent propagation are wired into an opt-in research
candidate. Method and policy appear in fitting provenance and the module is source-hashed.
Default analysis remains legacy; requesting the method without both research candidate and
forward uncertainty is rejected. Sparse-fix replay cannot supply it. Research CLI accepts
`--forward-reference matched`. Saved sessions yield sigma 0.0101930 rad (0.58402°), gain
0.925229 and R² 0.897332, with no science fit rerun.

Independent SciPy rotation fixtures include sub-degree bank oscillations, extra body yaw,
a larger transient, noisy GPS/IMU and slowly correlated gyro disturbances. Tests check
covariance, rotational invariance, noise-only abstention, gaps, duration and engine propagation
without fitting a science model. An eight-noise panel checks gross underestimation; it is
not coverage evidence. Focused integration checks passed 102 tests in 4.73s; 11 method checks
then passed in 0.37s after adding body-yaw/transient stress. No full suite or campaign ran.

Qualitative infrared-footage context reports a 135 mm lens and QHY585 mono camera at a
right-side passenger window, frequent apparent adjustments below a degree and occasional
larger view changes. No optical frames were ingested or converted to heading/bank; mounting
geometry, timing and calibration would be needed. This motivates both motion scales without
equating short variation with GPS error.

The [fresh matched pilot](matched-airline-pilot-20261006/README.md) freezes source
`82c882d2abf351cb0feb0e8efa237702d1deeccd475d682960419677bf479412`, one-thread environment,
C2 route, three candidates and fresh seed 600901. It proposes 18 evaluations; the separately
authorized initial three are now complete, with the remaining 15 unrun and unapproved. Plan hash:
`e3064a50835a631d6968b11757d8451cff1e87c20e9ae74bf02580f2fa06bf78`. Independent-error
covariance assumptions, latent-route realism and full-pipeline separation remain unvalidated.

### Completed matched-reference prefix and route screen

All three full-pipeline evaluations converged with zero analysis failures. The generating
condition was rotating-globe truth with `wind+bias_mixed` on the assumed 75-minute C2
FRA–JNB window, IMU turns 20/40/60 minutes, seed 600901, zero bootstrap. Candidates were
wind/exclude, wind-TAS/exclude and wind-TAS/model-and-compare. Source and plan hashes above
remain unchanged. The approved prefix is exhausted; status is `budget_complete`, both shards
are complete, and no worker is active.

The common matched reference passed with gain 0.7850611217, R² 0.7497273565 and estimated
sigma 0.01196597175 rad (0.6855996791°), supported by 67 covariance windows. This resolves
the previous reference exception for this condition, not uncertainty coverage. Retained cruise
was 57 minutes, elapsed support 69.333 minutes, retained heading span 15.464972°, four mount
epochs and maximum gap 582 seconds. Cruise duration and shared heading-diversity gates fail.
All primary and pairwise decisions abstain.

Fitted model-test ranks were 0/1/1; the conservative design-envelope rank was 0 for all three.
After SVD truncation every worst contrast retained fraction and information were zero. Before
truncation the existing wind candidate's worst retained fractions were 0.01944/0.09100/0.12364;
the physical candidate's were 0.02119/0.18374/0.20055, in rotating-vs-still, rotating-vs-disc,
still-vs-disc order. All remain below the unchanged 0.3122498999 retention threshold.
Corresponding untruncated information improved from 0.13543/4.05948/1.84434 to
0.16124/16.69905/4.96566. A rank-cutoff change alone would not fix this gate.

No magnetic boundaries were flagged. Retained/excluded coefficients and pair shifts were
identical (zero shift), but agreement was unavailable because both paths lacked identifiable
contrasts. The false agreement flag is not numerical disagreement or a mount-slip detection.
The physical speed-constraint chi-square was 74.968414, relative boundary margin 0.232470,
without a boundary flag. Neither result establishes a successful wind or mount correction.

Attempt times were 6.260351/72.624785/123.957378 seconds, sum 202.842514 seconds. Observed
two-worker wall time was 131.358896 seconds, measured from launch UTC to final status file
mtime on the original host. Saved run storage at review was 39,234,307 bytes. These are one
condition's zero-bootstrap costs, not calibration estimates. `results-review.json` in the
pilot corpus records results and provenance; `analysis/tests/review_matched_pilot.py` reads
the preserved campaign without rerunning inference.

`analysis/tests/review_route_geometry.py` additionally screened five explicit assumed C2
75-minute paths, sampling course at one second and applying the existing shared heading gate:
two 10° heading groups, each supported for at least 600 seconds and separated by at least 30°.
This optimistic screen applies no IMU, maneuver, magnetic or cruise-bin losses and performs
no simulation, fitting or SVD. AUH–ORD alone passes. Sampled spans are 96.86° ORD–AUH,
41.85° AUH–ORD, 19.98° ORD–LAX, 12.78° SEA–KEF and 24.97° FRA–JNB. ORD–AUH fails despite
wide overall span because distant heading groups are too short. Adequate raw heading duration
does not guarantee adequate retained geometry or nuisance separation. The next stage is a
route/window and turn-timing preflight before any newly budgeted full fit. No remaining case,
calibration or validation is authorized by this report.

### Observable route/turn preflight and extended-window proposal

No new flights, fits or SVD evaluations were run. `preflight_route_turns.py` mirrors the
analytic geometry's shared motion mask, ten-minute continuous qualification and full-minute
bin support, then applies the shared heading-duration rule and IMU-turn exclusions. It is
an assumed-kinematics screen, not the complete IMU/GNSS preprocessing or an acceptance bound.
Buffered turn checks use 120 seconds; the grid is five minutes, spacing at least ten minutes,
three turns with five-second motion and twenty-second recovery. No threshold was changed.

The original five windows all fail; their no-turn screened minutes are 30/0/41/61/57 in
ORD–AUH/AUH–ORD/ORD–LAX/SEA–KEF/FRA–JNB order. AUH–ORD exceeds the course limit for 845
sampled seconds, vertical limit for 1,169 and bank-rate limit for 950; counts overlap.
Joint-mask qualification has no ten-minute run. Omitting bank rate only for diagnosis yields
one 638-second run. Sparse-coordinate derivatives and reported height can contribute to these
losses; the report does not attribute them to measured aircraft motion. Bank rate belongs to
the maneuver mask; full cruise selection has different and additional criteria.

`preflight_route_windows.py` reads the two explicit normalized-track archives and checks all
192 overlapping 75-minute windows having at least 95% observed interval coverage. Provider
estimates and gaps over 90 seconds remain unusable. One FRA–JNB window fails for nonfinite
reported height. Seventy-three evaluable windows have at least 60 no-turn screened minutes;
9,640 safe three-turn schedules were enumerated in those windows. None passes. Only one
AUH–ORD window (41,400–45,900 elapsed seconds) passes both no-turn duration and heading,
with exactly 60 screened minutes before turn losses. Windows below 60 minutes are pruned
only on duration; heading-group failures are not used to prune because regrouping can change.

`preflight_extended_window.py` then checks 21 five-minute-grid extensions containing that
anchor, for durations 90/105/120 minutes. All evaluate, 19 have passing three-turn schedules.
The best 120-minute window is AUH–ORD elapsed seconds 40,200–47,400, observed coverage
0.99583333, turns 25/50/85 minutes, screened cruise 91 minutes across epochs 23/20/23/25.
The qualified heading-duration margin is 420 seconds; the 90-minute alternative has 69
screened minutes and only 60 seconds of heading margin. This exploratory selection is
conditioned on development screening and is not independent validation or science optimization.

The [extended pilot](extended-airline-pilot-20261006/README.md) freezes seed 600902 and the
same three candidate methods, with source `82c882d2...`, one-thread worker environment,
zero bootstrap and plan hash `d2337e3a4bbe4da89f9b446d9b49c7ca0f19f13d94172a0bb81861696549eae0`.
Its initial three tasks share rotating-globe truth and wind plus mixed bias. The separately
authorized prefix is now complete, as recorded below; the other 15 tasks remain unrun and
unapproved. The earlier pilots also remain complete and spent.

Reports are retained in the matched-pilot corpus as `turn-preflight.json`,
`turn-motion-review.json`, `window-preflight.json` and `extended-window-preflight.json`;
source/archive hashes accompany the helpers' outputs. Four independent focused controls
passed in 0.29 seconds, covering short runs separated by a gap, one-heading abstention,
buffered-maneuver refusal and heading-reference rotation. No full-suite rerun or calibrated
error/power claim follows from these screens.

### Completed extended airline prefix

The 120-minute AUH–ORD prefix (seed 600902, turns 25/50/85 minutes) completed with no analysis
failures and all nonlinear fits converged. Actual preprocessing retained 97 minutes across
97 bins and four epochs, elapsed support 117.333333 minutes, heading span 51.095929°,
maximum gap 520 seconds, latitude 42.443237–48.516658°N, speed 225.679357–250.296199 m/s.
The shared cruise-duration and heading-diversity gates pass. Actual bin selection differs
from the analytic screen's 91 minutes, so the preliminary screen is not a certified bound.

The matched forward reference passed: gain 0.9791684278, R² 0.9254233357, angle sigma
0.03823755676 rad (2.190850622°), with 112 covariance support windows. This covariance remains
unvalidated; it is not a measurement of device calibration accuracy. The envelope therefore
evaluates forward offsets up to ±0.1147126703 rad (±3 estimated sigma).

Fitted model-test ranks and conservative design ranks were all zero. Every intended primary
and pairwise contrast failed; all decisions abstain. Untruncated worst retained fractions,
ordered rotating-vs-still, rotating-vs-disc, still-vs-disc, were:

| Candidate | Retained fractions | Contrast information |
|---|---|---|
| Wind/exclude | 0.135268 / 0.048735 / 0.173710 | 11.153662 / 1.341455 / 5.454470 |
| Physical wind/exclude | 0.174659 / 0.077359 / 0.196523 | 18.726941 / 3.395131 / 7.002463 |
| Physical wind/model-and-compare | Same | Same |

All are below the unchanged 0.3122498999 retention criterion before truncation. Increasing
the kept singular subspace alone would not remove these failures. The physical candidate
preserves more information in this matched condition, but that does not establish useful power.
Design-envelope evaluations were 1,053 for wind and 10,530 per physical candidate. This
comparison does not isolate forward uncertainty, wind, bias and epoch nuisance contributions.

No watchdog boundaries were flagged. Retained/excluded paths gave identical coefficients and
zero pair shifts; agreement is unavailable because both fail identifiability, not because of
numerical disagreement or detected mount slip. Physical speed-constraint chi-square was
207.895981, relative margin 0.320117, with no near-boundary flag.

Attempt runtimes: 24.285724 / 147.287569 / 256.638571 seconds, sum 428.211864. Observed wall
time was 282.394589 seconds, launch UTC to final status mtime on the original host, and run
storage snapshot 49,961,789 bytes. `results-review.json` in the extended corpus records
provenance and individual outcomes; campaign SHA256
`270b5dc62022021bd8fc10d790100bdd48a723527c100f5e646dfee5ec6944bf`.
`run/status.json` is `budget_complete`, both shards complete, no worker active. The three-case
allowance is spent; the other 15 cases remain unrun. Neither calibration nor independent
validation was performed. Zero bootstrap and one shared generating condition cannot establish
error rates or coverage. Different routes and seeds between the 75- and 120-minute pilots
prevent a controlled duration-only comparison. The saved-diagnostic follow-up below separates
nuisance contributions; do not relax the acceptance gate or extend the spent allowance.

### Nuisance attribution and analytic course-gap repair

The [diagnostic review](extended-airline-pilot-20261006/DIAGNOSTIC_REVIEW.md) uses only saved
bins, axes and Jacobians. It reproduces recorded worst-retention states, checks nominal
anchors and zero-forward-offset controls, and allocates lost squared retention across all
nuisance-family orders. Physical speed rows remain; fitting priors do not enter the projection.
The two distinct saved Jacobians are reconstructed exactly within numerical tolerance; the
third candidate's saved tangent/parameters/row indices are identical. Four hundred subset
projections take 0.286s. Seven independent algebraic/physical controls pass in 0.19s.

At the nominal rotating anchor, physical-wind pre-cutoff retention is
0.185994/0.107847/0.199518. Removing bias drift for diagnosis gives
0.5262/0.2895/0.6058; removing wind gives 0.1886/0.1107/0.2011. No single group omission
restores all contrasts at the checked states. Bias drift dominates most all-orders loss
allocations. Zero forward offsets do not fix nominal overlap. Unpenalized tangents allow
arbitrary compensating amplitude; this is not evidence that real bias reaches that amplitude
or that all compensations satisfy nonlinear bounds/priors.

Raw geometry also limits rotating-vs-disc: mean east speed −206.754938 m/s gives north Earth
rotation +10.661420°/h and globe transport −6.663162°/h, net +3.998258°/h. The contrast has
horizontal RMS 5.531714°/h, vertical mean −13.379071°/h and vertical standard deviation
0.137925°/h. Same-side yaw rotations do not modulate the vertical component. Residual bias
level alone leaves pre-cutoff retention 0.309661 for this contrast, below 0.3122499.

During six fixed nominal turn controls, the analytic design tool exposed a separate bug:
course `np.unwrap` across NaNs poisoned all later supported data. The repair unwraps finite
runs separately, keeping full-bin gap/motion exclusions. Two regression cases pass (wind
and physical wind, 0.21s); four existing coverage/envelope/optimizer controls pass (0.84s).
Only original three turns and distributed six at 10/30/50/70/90/110 pass the buffered mask.
The six-turn physical candidate's worst nominal pre-cutoff retentions improve to
0.271480/0.124577/0.305099, all still below threshold. Four tested ten-minute patterns are
blocked by turns at 45, 75 or 95 minutes. This is a fixed-pattern nominal control, not
complete-envelope optimization, empirical acceptance or a deployed protocol.

Saved pilot/audit source remains `82c882d2...`. The analytic repair changes current source to
`a7cc619428f8a24f96e3ab77e5d99f1c5b1b92639b2f6c6e3cfed937176cf44f`; the turn-screen report
records both source versions. Old prospective manifests are stale. No full-suite rerun,
flight, fit, bootstrap, calibration or independent validation was performed in this diagnosis.
Next screen directionally different routes and feasible modulation patterns with the full
nuisance model; refreeze and budget only promising complete-envelope/full-pipeline comparisons.

`maneuvers.py` supplies the shared course-rate/bank-rate/climb/gap mask. Analysis checks the
integrated turn interval and excludes unsafe/unverified later epochs; geometry search adds
120 seconds of buffer. Optional diagnostics retain raw sessions, turn inputs, mount matrices,
pre-selection/orientation-qualified bins, final fit arrays and failure metadata.

`design_mode='envelope'` enables `nuisance-envelope-1`: all physical anchors, dynamic intercept/
drift combinations or wind-coefficient corners/drifts, ±3 forward sigmas and individual ±1°
mount epochs. Planning forward sigma is 5°. Fixed isotropic 3/6°/h noise changes information,
not retention: SVDs at 6°/h suffice; information at 3°/h is four times larger. Cutoff and
untruncated contrasts and limiting states are separate. Actual wind/dynamic crab knots are
900/300 seconds; the historical timing audit used 300-second wind knots. This finite grid
does not bound all nuisance trajectories or remove preprocessing dependence on gyro data.
Geometry search uses beam 16 and worst dynamic/wind eligibility, margin, then information.
Known assumed axes still require complete-pipeline confirmation.

Five prepared routes have observed-fix and simulated-high-rate replay specs; two remain blocked.
PCHIP is restricted to short observed intervals; estimated positions/long gaps split support.
Reported height is assumed geometric. Wind preserves ground geometry and changes the air vector.
The original lane preserves missing accuracies. Both harness and analyzer refuse empirical
replay policies pending validated position/timing uncertainty and an approved replay domain.
New composable adversaries are wind+mixed bias
and wind+mixed bias+correlated+thermal with independently named component RNG streams.

`pairwise_method='profile'` requires the envelope and implements `pair-line-profile-1` along
`k_b + theta (k_a-k_b)` with endpoints 0/1. It uses the untruncated envelope difference and
its own free/endpoint nesting, nonlinear bootstrap and widened-prior checks, independent of
global-rank eligibility. Integrity/selection checks remain. Flight threshold keys are
`[candidate_id, variant, comparison, method]`; diagnostic rank is one. Pooling uses
`pair-line-profile-reml-hk-1`, keeps repeated sessions within units and rejects mixed methods.
Version-2 policies declare statistic methods. Fresh calibration is required; analytic
endpoint p-values and uncalibrated winners remain development diagnostics.

Preparation freezes 2,160 unrun evaluations and search bounds, with zero execution allowance.
The ±10-minute controls violate spacing and are blocked; unsafe retained controls must abstain.
New runtime/storage are unmeasured. Historical calibration plans are stale for this source.
**177 focused checks passed in 5.97s** for that source freeze. Physical wind/TAS was subsequently
implemented as described below, followed by modeled magnetic ambiguity and observable-domain
enforcement and the sharded runner. Default three-model
rules and the science cutoff are preserved apart from the new orientation integrity safeguard.

## Physical wind/airspeed candidate and CI repair, 2026-10-06

The opt-in `crab_model='wind_tas'` candidate models north/east wind and log true airspeed
at 900-second knots. The air vector is the observed ground vector minus wind; its direction
and analytic turning rate supply crab and crab-rate predictions. A conditional residual
`(norm(ground-wind)-TAS)/2 m/s` checks speed consistency. TAS is latent, not a separate
airspeed observation. The constraint must not be interpreted as independent heading evidence.

`wind-tas-1` freezes 20 m/s wind-level and 10 m/s/hour wind-change priors, a 250 m/s TAS
reference with 0.2 log-level and 0.08/hour log-change priors, component wind bounds ±60 m/s,
TAS bounds 120–350 m/s and minimum observed ground speed 100 m/s. These are provisional
development assumptions, not measured airline uncertainty bounds. Priors on wind, its rate,
TAS and its rate are separately widened for sensitivity checks. Free, fixed-model, global
and pair-line fits include the speed residual, nonlinear derivatives and bounds. A fit within
1% of a bound causes abstention for its test. Requested bootstrap requires complete nonlinear
refits and holds GNSS fixed; it does not propagate unknown public-track position errors.

The primary test checks its free/fixed/profile boundaries. Direct pair profiles check their
own free/endpoints and retain their own convergence, prior and bootstrap gates. Physical
candidate eligibility has a distinct version; old empirical policies cannot be reused.
Diagnostics retain the physical curves and speed-constraint objective. Existing fit-row
arrays remain gyro rows, not an export of the augmented speed-constraint Jacobian.

The physical design envelope checks 13 bounded wind corner/drift states crossed with five
TAS level/drift states, all model anchors, forward-angle and mount-epoch perturbations.
Both 3 and 6 degrees/hour gyro noise levels are explicitly evaluated because the fixed speed
constraint prevents uniform scaling of the augmented information. Search can include this
candidate in its worst-case nuisance-model set. The finite grid does not certify the entire
bounded nuisance space. The independent wind-truth generator is unchanged.

Controlled checks cover analytic derivatives, known wind triangles, agreement with the
independent wind simulator, bounded/nested profiles, geometry independence from measured gyro,
eligibility and the public fit entry point with an intentionally insufficient bootstrap.
No matched campaign, optimizer search, fresh calibration or independent validation has run.

GitHub Python run 37465056735 failed four existing turn/crab regressions while 321 passed.
The maneuver guard's second derivative amplified GNSS course noise. The repair uses the same
30-second smoothing window as course-rate estimation; yaw, bank, coverage and integrity limits
are unchanged. A realistic position-noise regression was added, and the four previously failing
checks pass locally. Earlier prospective proposals and route masks are historical for their
old source and must be refrozen before execution.

The complete Python CI suite passed locally outside the sandbox: **336 passed in 282.13s**,
with one Starlette dependency deprecation warning. A 45-second diagnostic reproduced the
sandbox-only stall in the concurrent-upload async transport; all 13 server checks passed
outside it in 12.26s. No server behavior or concurrency assertion was changed.
The [physical-wind comparison preparation](wind-tas-development-20261006/README.md) freezes
54 unrun evaluations on a supplied airline route, with combined nuisance cases. Its 20/40/60
minute schedule passes the revised buffered assumed-geometry mask but is not optimized or
certified through reconstructed orientation. Execution allowance remains zero.

## Magnetic ambiguity follow-up, 2026-10-06

The [two-path research candidate](magnetic-ambiguity-development-20261006/README.md) is
implemented and opt-in. `MountYaw` adds an offset and a finite-duration linear yaw rate for
each flagged segment/mount epoch. The offset persists within that epoch; the rate stops at
the segment boundary. In the gyro prediction it subtracts from crab azimuth/rate, giving
positive IMU yaw a positive rate about up. Both angle and rate derivatives participate in
weighted nuisance projection, nonlinear fits, profiles, bounds and prior sensitivity. First
flagged boundary bins are excluded to avoid an unmodeled instantaneous angular impulse.

The finite envelope adds nominal and individual ±3-sigma mount offset/rate states, using
the same provisional policy as fitting. It does not evaluate the full Cartesian product of
all mount states. The retained fit is compared with an actual rerun of the original exclusion
path, including independent preprocessing, forward uncertainty and WMM selection sensitivity.
Public scientific eligibility requires both paths to be eligible, identical endpoint decisions
and compatible estimates; pair gates remain independent of global rank. Missing/invalid decisions
and unavailable controls fail closed. The retained/excluded agreement uses development diagnostic
thresholds only. Applying empirical policies and non-development harness runs is refused until
a dual-path calibration design exists. There is no production promotion.

**119 focused checks passed in 15.90s**; the previous committed source `db28900` passed the
full 336-test suite. No new campaign or search was run and no performance improvement is claimed.
This source/policy extension invalidates earlier prospective manifests, including the wind/TAS
comparison prepared before it. Preserve historical artifacts and refreeze before any approved run.

## Observable-domain enforcement, 2026-10-06

The [domain contract](flight-domain-development-20261006/README.md) binds primary and flight
pairwise empirical policies to `observable-flight-domain-1`, with canonical identity, explicit
finite observable bounds, retained mount-epoch timing and a single acquisition lane. The
analyzer derives that lane from the recording; synthetic/recorded GPS and both replay modes
cannot share a domain. Membership uses retained geometry rather than fitted science coefficients.
The same recomputed membership gates research, calibration, validation and threshold application.
Missing/inconsistent/outside bindings abstain; diagnostic fits remain available.

New primary policies are `empirical-decision-5`; flight pair policies are `pairwise-empirical-3`.
Their operational strata include `domain_id`. The harness freezes `--flight-domain` content,
and validation must match calibration exactly. Direct profiles preserve rank independence;
their comparison/method threshold keys are no longer misread as global-rank campaign cells.
Historical unscoped artifacts remain offline research records and cannot issue empirical flight
decisions. No domain has been scientifically approved and no new threshold has been calibrated.
Public-track empirical analysis and magnetic dual-path empirical decisions remain refused;
summary pooling needs separate domain work. Prior prospective freezes are stale.

**156 focused checks passed in 29.71s**, followed by **70 domain/eligibility/hardening checks
in 1.14s** after adding the domain module to the scientific source freeze. Those checks include
a regression proving a domain-module change alters the frozen hash. The earlier 336-test full
suite applies to `db28900`, before magnetic/domain changes. No campaign, search or new full-suite
run occurred in this stage.

## Durable sharded execution, 2026-10-06

The [runner contract](sharded-campaigns-20261006/README.md) implements deterministic implicit
flight tasks bound to exact candidate jobs, source/configuration/policy/environment and fixed
shards. The research harness's `--write-sharded-plan` prepares without executing; runtime requires
an explicit total attempt prefix, with at most two single-thread workers. Fresh subprocesses
initialize numerical thread limits before NumPy/SciPy imports. Source/environment changes stop
the run before a result is committed. Existing freezes need renewal; the old two-thread
environment cannot be reused for these workers.

Hash-chained shard journals fsync starts and completions. Resume preserves successes/failures
and records a lost started attempt as an infrastructure failure rather than fitting it again.
Incomplete final bytes are archived before tail repair; malformed complete records are rejected.
Locks exclude duplicate workers, live merging and orphan replacement. An explicit detached launch
supports terminal/chat disconnection. Merging streams all records in task order, checks provenance
and duplicates, and retains failures. Partial exports cannot become holdout evidence. No stopping
depends on acceptance or model outcomes. Existing calibration precision and exact-bound rules
remain; no threshold or scientific decision is automatically created by the executor.

No flight simulation, optimizer search, calibration or validation ran during this implementation.
Actual campaign speedup/storage remain unmeasured; additional compute allowance remains zero.

**94 focused checks passed in 6.90s** across runner, domain, eligibility, research hardening and
existing worker recovery. Two OS processes wrote fixture records; a fresh interpreter checked
one-thread setup before numerical imports. These are software checks, not flight/tail evidence.
The earlier full suite remains historical and has not been rerun after the subsequent extensions.

## Airline assumption review and refreshed pilot, 2026-10-06

The [preparation record](airline-pilot-preparation-20261006/README.md) reviews five existing
assumed route paths without flight synthesis, fitting, SVDs or schedule search. The 20/40/60
minute control passes the buffered mask on FRA–JNB and SEA–KEF, and fails on the three supplied
route windows; failures remain recorded. Prescribed wind and sampled-knot log-TAS interpolation
give a FRA–JNB speed mismatch median 2.95, p95 11.41 and maximum 20.68 m/s across supported
path samples. These include potentially excluded intervals and are not optimal-spline residuals.
None of the 65 independent wind/TAS grid states is within 6 m/s at every sample on any reviewed
path. Off-manifold states remain in the finite envelope; no constraint, grid or cutoff changed.

This identifies an assumption to test: a 2 m/s conditional speed constraint plus 15-minute TAS
knots may interact with assumed public-position interpolation. No independent airspeed/heading
exists, and the review does not prove failure or establish real motion between observations.
Six preparation checks passed in 1.07s and explicitly prohibit flight fits/SVDs.

The new one-thread sharded proposal freezes seed 600900, FRA–JNB dense simulated GPS, three truths,
wind+mixed bias and wind+mixed bias+correlated+thermal, and wind/exclude, wind_tas/exclude and
wind_tas/model_and_compare candidates. It has 18 matched evaluations, zero bootstrap and zero
authorized execution. The initial proposed prefix is three evaluations of the same rotating
truth/wind-plus-bias condition to measure current time/storage before further budget decisions.
No wall-time quote or limit is invented from old runtimes. The remaining 15, true-slip controls,
other routes/modes, search and nonzero bootstrap remain separately scoped. The scientific source
is unchanged from the sharded-runner freeze. No scientific domain, threshold or policy is promoted.

## External flight tracks and missing GNSS

The collection app now requires a selected operating airline, its flight number, the scheduled
origin-local departure date and route codes. The directory is available offline and includes
historical carriers. Format-valid entry, directory membership and opening a flight-history link
do not verify a flown flight. Actual identity/date/route verification remains a manual provider
record check, separate from instrument provenance and scientific eligibility.

An acknowledged missing fix permits IMU recording; GNSS logging continues if reception returns.
Phone-clock anchors at creation and flight start/resume help document timing but do not establish
UTC accuracy. External browser lookup is user-initiated and separate from upload consent.
See [PROTOCOL.md](PROTOCOL.md), [FORMAT.md](FORMAT.md) and [PRIVACY.md](../PRIVACY.md).

The [supplied](flight-geometry-20261006/README.md) and
[publicly extracted](scraped-flight-geometry-20261006/README.md) position tracks are development
geometry artifacts. Import/extraction preserves source labels, estimate flags, missing values,
gaps and timestamp provenance. That establishes parser behavior, not scientific GPS-fallback
validation. The present analyzer does not accept these tracks as substitutes for phone GNSS,
and they supply no IMU, wind or sensor-calibration evidence.

Before an external-track method can support scientific conclusions, its policy must define:

- Matching of operating flight/date/route and the recording's actual time interval, including
  origin-local versus UTC day boundaries and codeshare ambiguity.
- Independent clock alignment and position/timing uncertainty, without alignment or source
  selection based on gyro agreement or which physical model wins.
- Observed-coverage, gap and sampling requirements that preserve uncertainty in course changes
  and maneuvers; provider estimates are not measured fixes. Missing GNSS accuracy/satellite fields
  must not be invented, and reported altitude needs an established reference or uncertainty.
- A frozen source-selection/gap policy, retention of the immutable original session and separate
  provider provenance, followed by calibration and independent validation covering that source.

This is additional analysis work. Completed development campaigns used their original simulated
GNSS assumptions and make no external-track recovery claim. Collection may preserve a useful
recording without guaranteeing admission under `pilot-2` or `candidate-eligibility-2`.

## Research candidates and independent campaigns

The opt-in candidate implementation adds continuous piecewise-linear crab (five-minute knots,
amplitude and rate priors), axis or axis-by-segment residual weighting, measured forward-angle
uncertainty, and full nonlinear bootstrap refits. Production still selects the historical
constant-crab/global-noise implementation. Candidate methods and empirical decision rules are
excluded from primary observational pooling. Mixing inference configurations or decision policies
in one collation raises an error; reprocess consistently or collate the groups separately.

Candidate eligibility is **candidate-eligibility-2**, owned by `lll.policy` and shared by
analysis, collation, research, calibration and validation. It replaces the curvature-only
exclusion with all three named design model contrasts meeting the frozen retention threshold,
requires positive model-test rank and converged inference, and requires valid bootstrap
convergence whenever bootstrap was requested. Missing required diagnostics fail eligibility.
Other scientific exclusions, provenance and bench gates remain applicable. Individual-term
identification flags remain diagnostics. The default legacy analysis retains **pilot-2**;
candidate scientific eligibility does not promote a candidate into primary observational pooling.
Results and research records carry eligibility version/hash provenance; manifests and empirical
decision policies freeze both eligibility policies. Old candidate campaigns and decision files
must be regenerated and recalibrated; mixed or mismatched policies are rejected.

`lll.inference_policy` owns the systematic floor and candidate defaults. Its version and content
hash, resolved settings and configuration hash accompany each fit. The 0.02 rotation floor was
tuned on historical hardware-fault simulations; those runs are **development evidence only**.
The software version remains 0.6.0; Python packaging, FastAPI and Android now obtain it from
`lll.__version__`. Candidate identity is tracked separately from software and eligibility policy.

Research partitions are enforced in both harnesses:

| Partition | Seed range | Purpose |
|---|---|---|
| development | 0–999999 | debugging, selection and tuning; includes all historical runs |
| calibration | 1000000–1999999 | estimate thresholds after selecting a candidate |
| validation | 2000000–2999999 | evaluate the frozen rule once |

Seeds independently determine geometry, deliberate-turn protocol, missingness, nuisance draws,
sensor noise, bootstrap and pooling. Design version 2 separates turn timing and GNSS gaps from
geometry. An explicit `--turn-schedule` (minutes into flight; an empty list means no turns)
overrides simulated turn timing without changing route, missingness or sensor-noise inputs.
Use `--turn-min-spacing` and `--turn-edge-margin` to reproduce custom optimizer constraints.
Recorded version-1 designs remain replayable with their original five streams.
Paired candidate comparisons share the complete simulation design. Replays are explicitly marked
and cannot serve as new calibration or validation evidence. Reserve a new, unused validation seed
cohort after any retuning; the harness enforces partition boundaries, while the campaign operator
must maintain the history of consumed validation cohorts.

The research CLI defaults to one seeded route, one sampling/block setting and 20 replicates.
Seeded routes vary latitude (±70°), longitude, 2–6 bearings, 10–45-minute legs, index-turn timing
and GNSS gaps. Weak geometries remain in the results with their exclusion reasons. Fixed routes
and named equator/high-latitude/dateline fixtures remain available. Interaction scenarios are
`crab_long_drift`, `correlated_thermal`, `forward_crab`, and `turn_dropout_drift`; `fuzz` draws
bounded nuisance parameters. Forward-axis error is injected into the estimated axis after
simulation, explicitly recorded in `analysis_options`; it is an estimator stress test.

Each flight record stores all simulator defaults and overrides, a serializable crab trajectory,
all random streams, inference options, runtime, raw model statistics, gate exclusions and failures.
`--replay FILE` reconstructs those inputs. Summaries separate truths, scenarios, candidates,
partitions, geometry modes and sensor variants, with coverage, bias, variance and rejection rates.

Example development comparisons (estimate runtime from a small pilot before expanding):

```sh
~/venv/bin/python analysis/tests/research.py --scenario drift+1 --truth all --seed 10000 --geometry seeded --same-side-up-turns --crab-model constant dynamic --noise-model axis_segment --bootstrap-refit nonlinear --sampling segment --blocks 15 --bootstrap 2 -o /tmp/candidate-pilot.json
~/venv/bin/python analysis/tests/research.py --scenario smooth --research-candidate --crab-model dynamic --crab-rate-sigma-dph 0.5 1 2 --forward-uncertainty --bootstrap 2 -o /tmp/prior-pilot.json
~/venv/bin/python analysis/tests/research.py --scenario pool --truth all --units 3 5 10 --bootstrap 20 -o /tmp/unit-pilot.json
```

Axis/segment variances shrink toward global variance by 20 equivalent bins. Candidate weights
come from a preliminary free nonlinear fit and remain fixed for all model comparisons and
prior checks. Bootstrap resampling operates on centered, standardized residual vectors and restores
destination scales, preserving dependence across axes. `segment` sampling never crosses a segment
or time break; `moving` remains available for comparison. Both local and nonlinear refits use
total-parameter priors. Nonlinear mode refits free and fixed models for every null replicate;
failed replicates, requested counts and effective counts are recorded explicitly. Failed nonlinear
refits retry deterministically from the reference fit, free fit, preliminary fit and default
initialization. Bootstrap calibration requires at least 20 attempts and 95% success for the free
and every model-null group. Results expose success fractions and `bootstrap_valid`; invalid runs
retain analytic diagnostics but provide no bootstrap-calibrated or empirical model decision.

Forward-axis uncertainty uses the horizontal roll/bank regression with a 10-lag Newey-West score
covariance, then normalization/projected-angle propagation. The single measured angular parameter
is shared in the reference mount frame and transformed through mount epochs. This does not estimate
uncertainty in the gravity axis or validate the regression against all systematic errors. A missing
or degenerate angle uncertainty makes the candidate unavailable instead of silently using zero.

Calibration/validation require an exact frozen manifest, including source hashes and the actual
Python/NumPy/SciPy versions and declared `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS` and
`MKL_NUM_THREADS` settings. Decision policies freeze the same numerical environment; validation
rejects a campaign, record or policy produced under different versions or thread settings. Use
`--write-manifest PATH` with the complete proposed command configuration; it writes only the
manifest. Repeat the command with `--manifest PATH` after reviewing and approving campaign cost.
`--seeds` preregisters the attempt count. The manifest computes the validation accepted-sample minimum using
the same exact beta bound as assessment, with the complete family size, `--tail-confidence`
(default 0.95) and `--allowed-failures` (default zero). `--tail-min-accepted` may increase this
minimum. `--development-campaign FILE` supplies measured acceptance and runtime estimates,
using the minimum diagnostic/truth cell acceptance and including failed attempts; without a
pilot, cost estimates are explicitly unavailable.
Calibration has its own minimum: `--calibration-tail-observations` defaults to 30, with
`--calibration-tail-confidence` 0.95. Exact binomial inversion requires at least that many
observations in the target tail with the requested probability: **14,640 accepted samples**
per null/diagnostic cell at alpha 0.0027 (39.528 expected tail observations).
`--calibration-min-accepted` may increase this minimum; it cannot reduce the frozen precision
objective. Calibration and validation counts, their separate costs and their combined cost
are recorded in the plan. Pairwise null tests increase the simultaneous validation family
without multiplying flight attempts unnecessarily: the same flight supplies several comparisons.
Source, configuration or numerical-environment changes invalidate the manifest.
Campaign provenance hashes the scientific source directly; optional `LLL_GIT_COMMIT` supplies a
build's commit identifier without analysis invoking git.

Calibration can reserve a rejection-rate margin with `--calibration-alpha`, for example
0.00135 while retaining the claimed rate 0.0027. This estimates a more conservative threshold
and sizes calibration at the actual target tail; 30 tail observations with 95% probability
then require **29,285 accepted samples** per null/diagnostic cell. Validation still assesses
the claimed 0.0027 rate. The target and claimed rate are separately frozen in the decision file.
The default remains 0.0027. This costs power and additional calibration runs.

A zero-failure validation plan has little chance of passing when the true rejection rate
equals the claimed bound: with a nine-test family, the minimum 1,921 accepted flights have
only about 0.56% probability of zero failures at rate 0.0027. Optional
`--validation-design-rate RATE --validation-power 0.90` sizes a sufficient nonzero-failure
plan using exact binomial power, a union bound over the full validation family and the same
simultaneous confidence bound. It doubles the
failure budget until sufficient, rather than claiming a globally minimal plan. The design
rate is a planning assumption, not measured evidence; independent validation still must pass
the exact bound. Freeze these options before calibration and repeat them for validation.

After a calibration campaign with sufficient accepted flights per truth and stratum:

```sh
PYTHONPATH=analysis:server ~/venv/bin/python -m lll.research_calibration calibrate calibration.json -o decision.json
```

This selects each truth's `1 - calibration_alpha` quantile using the higher order statistic
(0.9973 by default). Candidate fits use
the objective difference for identifiable constraints; legacy fits retain their raw objective
statistic, explicitly named per operational cell. Diagnostic strata include scenario and simulated
geometry. Operational strata include candidate identity, sensor variant and observed `model_test_rank`.
The operational cell is selected after fitting, including separately for the WMM sensitivity fit.
An uncalibrated rank abstains instead of borrowing another rank's threshold. Their threshold
is the maximum across the preregistered diagnostic strata, so a flight needs no synthetic scenario
label. Independent assessment checks each diagnostic stratum separately, retaining the complete
Bonferroni family. Freeze the validation
manifest with `--partition validation --decision-policy decision.json` and the chosen sample counts,
then run it after cost approval. The empirical rule is applied inside analysis, including the WMM
sensitivity gate, so validation measures acceptance under the actual rule. Calibration acceptance
uses the original diagnostic rule; only independent validation establishes the new gated rule's rate.

```sh
~/venv/bin/python -m lll.research_calibration assess validation.json --policy decision.json -o assessment.json
```

Assessment requires every claimed truth/stratum's simultaneous one-sided 95% upper bound to be
at most 0.0027 (Bonferroni over the claimed family), plus its preregistered accepted-sample minimum.
Insufficient acceptance is inconclusive. Threshold files remain experimental even after assessment;
production promotion is a separate reviewed policy revision. No tail campaign is run automatically.

## Identifiability and experimental design research

Inference policy **inference-3** adds observation-weighted science-space diagnostics to the
candidate engine. It whitens the Jacobian with the weights frozen from the free fit, removes
the unpenalized nuisance column space, then SVDs the residual science columns. Nuisance priors
cannot supply information in this calculation. Rank selection normalizes each science column
by its original weighted norm and retains singular values at least `sqrt(1 - 0.95²)`. This is a
provisional research cutoff derived from the existing likeness limit, not a validated rank rule.
Reported combinations and singular values are converted back to dimensionless k coordinates.
Unmeasured individual coefficient uncertainties are `null` in the observation-only report.

Candidate acceptance now uses a separate `design_identifiability` report. It evaluates the
unpenalized nuisance tangent space at all three science-model anchors, with zero crab/forward
angle offsets and a frozen uniform 3 °/h bin-noise assumption. Each comparison uses its worst
retention and information across the anchors. Neither fitted gyro coefficients nor preliminary
residual weights enter this calculation. The report records its assumptions and per-anchor
spectra; it describes local tangent identifiability conditional on the retained trajectory and
configured nuisance bases, rather than a guarantee over arbitrary nonlinear nuisance histories.
The free-fit SVD remains a diagnostic and defines the profiled model-test subspace and observed
test rank, whose null distribution is calibrated in its own operational cell.

Results include `estimable_rank`, `singular_values`, `normalized_singular_values`,
`condition_number`, `estimable_combinations`, and `model_contrast_information`. Model-separation
information measures the retained signal difference between each pair of models; it also reports
whether the corresponding coefficient contrast itself is estimable and its standard error.
The shared candidate policy checks the three design model contrasts instead of the individual curvature gate.
Prior sensitivity is evaluated in the retained combinations. Legacy production eligibility is unchanged.

Candidate model tests constrain only the retained combinations to the tested model's values,
leaving other science directions free and refitting the nuisance parameters. The profiled
objective difference is `delta_chi2_identifiable`; its asymptotic degrees of freedom and bootstrap
inflation use `model_test_rank`. Rank zero produces no rejection decision. `tested_contrasts` and
`unobservable_contrasts` show which pairwise distinctions the flight supports. Full fixed-model
objectives and `delta_chi2_raw` remain diagnostics. These nonlinear tests still require independent
empirical calibration. New source hashes invalidate earlier frozen campaigns.

`--model-test-ranks` preregisters the candidate rank envelope (default 1, 2, 3).
Every declared rank must obtain enough accepted calibration samples; use development evidence
to choose a supported envelope before freezing. Missing declared cells cannot silently disappear.
The development-only cutoff sweep reads existing spectra without refits:

```sh
~/venv/bin/python -m lll.rank_sweep /tmp/development.json -o /tmp/rank-sweep.json
```

It reports rank changes over a configurable cutoff grid and proximity to the baseline boundary,
with separate attempted/analyzed denominators. `--rank-min-relative-margin` optionally requires
distance from that boundary relative to the cutoff; its default zero leaves this extra restriction
disabled. Select any positive margin on development evidence, then preregister it before calibration.

`optimize_turns.py` searches zero through six same-side-up 180° turns with a deterministic beam
search (default beam width 16). It uses a five-minute grid, ten-minute minimum spacing and
five-minute edge margins, all configurable. Every schedule uses the same seeded route, missingness
and nuisance history across all three truths and both dynamic and wind crab fits, with dynamic
sensor bias and segment weights. `--crab-models` can explicitly restrict the nuisance-model set.
The score first requires all three intended contrasts to be estimable in every evaluation,
then maximizes the minimum retention margin above the policy threshold, then the minimum
contrast information. Failed fits or missing/nonfinite diagnostics rank below valid evaluations.
Equal scores prefer fewer turns, then lexicographic schedule order. Schedule evaluation uses two free fits to determine frozen weights
and the local Jacobian; model tests, bootstrap and prior sweeps are omitted in this design-only
mode. Outputs include the best schedule, the frontier by turn count,
per-schedule scores, the limiting evaluation, per-flight diagnostics and source/policy provenance.
If no schedule passes, `best` is null and `best_diagnostic` retains the highest-ranked schedule;
`feasible_winner` explicitly states feasibility. This design-only score checks identifiability;
full-flight acceptance still requires the complete eligibility policy, and information is a power
proxy rather than a calibrated power estimate. The heuristic does not
guarantee a global optimum. Estimate cost before running a search:

```sh
~/venv/bin/python analysis/tests/optimize_turns.py --routes 2 --estimate-only -o /tmp/turn-cost.json
```

Cost estimates include both crab models, the beam width and both free fits per evaluation.
Supply complete measured design-evaluation seconds with `--pilot-evaluation-seconds` for a runtime
estimate including simulation and anchor SVDs. `--pilot-seconds` retains the narrower free-fit-only
estimate; its output explicitly excludes that overhead. Removing `--estimate-only` runs the search
and should follow cost review.
Named adversaries now include `bias_step`, `bias_ramp`, `bias_rw_high`, `bias_settling`,
`bias_very_long`, and `bias_mixed`. The existing bias-knot and random-walk-scale list options form
a matched grid; summaries report coefficient RMSE, accepted fraction, false rejection and power
to retain the true model while rejecting every wrong model among accepted flights. Successful
fits that abstain from a decision remain in coefficient diagnostics and have a separate count.

The independent `wind` simulator holds true airspeed fixed, evolves north/east wind slowly and
solves the wind triangle on each course, changing both ground speed and crab. The opt-in
`--crab-model wind` fits `a(t) sin(psi) + b(t) cos(psi)`, including the full heading derivative.
Its coefficients use fifteen-minute knots by default, compared with five-minute knots for the
time-only dynamic crab candidate. Override either with `--crab-knot-seconds`:

```sh
~/venv/bin/python analysis/tests/research.py --scenario wind --truth all --crab-model dynamic wind --bias-model dynamic --bootstrap 0 -o /tmp/wind-pilot.json
```

Pooled empirical diagnostics resample whole IMUs, retain all member flights, null-center coefficient
vectors, assign repeated draws distinct unit identities, and recompute the hierarchical covariance
and studentized statistic. They report `(exceedances+1)/(replicates+1)`, Monte Carlo intervals and
failures alongside the approximate F diagnostic. Fewer than three units or singular covariance
makes this unavailable. Many replicates cannot compensate for very few physical units. Neither
method establishes pooled 3σ validity without independent campaigns across unit counts and effects.

The legacy `coverage.py N` and `coverage.py --null N` commands are explicitly development-only.
For partitioned coverage, use `coverage.py --partition ... --manifest ...` with research options;
it delegates to the same enforced campaign implementation.

## Regression checks

### Candidate integration pilot, 2026-10-05

[Paired flight records](research-candidates-pilot-060.json) contain 18 analyses: three truths,
three scenarios (`drift+0`, `drift+1`, `crab_long_drift`) and two methods, using development seed
10000, seeded geometry, same-side-up turns, SPP, 15-bin blocks and two bootstrap replicates.
The legacy method uses constant crab/global noise/moving blocks/local refits. The candidate uses
dynamic crab/axis-by-segment noise/segment blocks/nonlinear refits with forward-angle uncertainty.
These are paired runs of nine simulated conditions, not 18 independent flights or a comparison
isolating any single inference change. Total elapsed time was 257.4 seconds.

| Scenario | Accepted, each method | True-model rejections, each method | Rejections among accepted, each method |
|---|---:|---:|---:|
| zero crab drift | 2/3 | 0/3 | 0/2 |
| +1°/h crab drift | 2/3 | 0/3 | 0/2 |
| +1°/h crab + long sensor drift | 1/3 | 3/3 | 1/1 |

All analyses converged, with no recorded bootstrap failures. The accepted interaction failure is
the **still-globe truth under both methods on the same fixture**. Its reported true-model p-values
were 0.000643 (legacy) and 0.0000291 (candidate), both below the nominal 0.0027 threshold. Both fits
excluded the rotating-globe and flat-disc interaction cases for lack of curvature identification;
the legacy flat-disc case was also prior-dominated. This pilot does not support promoting the
candidate or asserting that the gates prevent false rejection under combined faults.

The two-replicate bootstrap only exercises integration: its variance and mean-inflation estimates
are unstable, and its empirical 3×3 covariance is rank deficient. Do not interpret the stored
bootstrap covariance coverage diagnostic as joint 95% coverage. These pilot p-values are outputs
under the explicitly reduced replicate count, not calibrated significance or results for the
production default of 300 replicates. A separately approved follow-up should first repeat this
preserved development fixture with adequate bootstrap counts, then vary seeds, geometry and priors.
Do not tune on the final validation partition.

[Pooled records](unit-bootstrap-pilot-060.json) cover all three truths at 3, 5 and 10 units, with
20 whole-unit bootstrap replicates per tested null. All nine cases completed in 2.95 seconds,
with no bootstrap failures and no analytic or empirical true-model rejections. The empirical
p-value cannot fall below 1/21 at this replicate count, so the absence of empirical 3σ rejections
is guaranteed by its resolution and supplies no tail evidence.

The implementation's focused suite passed 62 tests before these pilots. No holdout campaign,
threshold calibration, hardware validation or production-method promotion was performed.

### Investigation of the accepted false rejection

The implementation and initial pilots were committed and pushed as `bb20798`, after incorporating
the remote README update. The following experiments remain development diagnostics on the same
preserved still-globe fixture (seed 10000); they do not add independent validation observations.

[Legacy reproduction with 300 replicates](false-rejection-legacy300-060.json) confirms that the
accepted false rejection is not just a two-replicate pilot artifact. It converged and passed every
gate, with true-model p = 0.00010945. The free-versus-true-model raw objective difference was 24.1517;
lag-1 residual correlation was only 0.0717, giving an effective-sample scaling factor of 0.8661.
The true-model bootstrap mean-inflation factor stayed at its lower bound of 1.0. The reproduction
took 4.03 seconds on the recorded environment.

[Matched fault-removal controls](false-rejection-ablations-060.json) retain geometry, sensor seed,
turns, dropouts and inference settings, with 300 moving-block bootstrap replicates:

| Injected time dependence | True still-globe p | Gates | Outcome |
|---|---:|---|---|
| crab drift only, +1°/h | 0.340873 | pass | truth retained |
| sensor drift only, 90-minute period and (3, −2, 4)°/h amplitudes | 0.000193893 | pass | truth rejected |
| both effects | 0.000109452 | pass | truth rejected |

The long sensor drift is sufficient to produce the failure; the interaction with crab drift is
not necessary on this fixture. [Block-length checks](false-rejection-blocks-060.json) at 5 and 30
bins also retained the accepted rejection with p = 0.000109452, matching the 15-bin reproduction.
These checks took 14.0 and 18.5 seconds respectively; no threshold or systematic floor was adjusted.

[The candidate reproduction with 300 full nonlinear replicates](false-rejection-nonlinear300-060.json)
also converged and passed all gates, while still rejecting the true still-globe model at
p = 0.0000290647. All 300 free-fit bootstrap replicates and 300 null replicates per model completed
without recorded failures. Its lag-1 residual correlation was zero after clipping; every bootstrap
mean-inflation factor remained at the lower bound of 1.0. Thus its reported p-value matched the
two-replicate pilot even after the much larger refit. Runtime was 548.5 seconds (9m09s), longer
than the initial estimate; use this measurement when costing further nonlinear campaigns.
Neither method's accepted false rejection disappeared at the higher bootstrap count.

[Paired response decomposition](false-rejection-decomposition-060.json) compares the crab-only and
combined cases without bootstrap, on the same 70 retained bins. Adding sensor drift changes the
calibration-corrected response by 2.325°/h RMS. After refitting, the change remaining in residuals
is 1.463°/h RMS: 60.4% of the added response's squared magnitude is absorbed by the fitted mean
(model signal plus residual bias). The inferred coefficient changes are −0.1816 in globe rotation,
−0.1209 in curvature, and +0.4423 in disc transport. The RMS change in fitted model signal alone
is 2.238°/h. These are descriptive paired differences, not an independent variance estimate.

The code and controls support an omitted-bias-dynamics explanation: calibration supplies a linear
interpolation between pre/post bias estimates, and the fit adds a constant residual bias per gravity
orientation. Neither represents this oscillating sensor bias. Dynamic crab and forward-angle
uncertainty represent different physical effects. Once the free fit absorbs part of the drift into
model coefficients, resampling its residuals does not reconstruct that absorbed component; a small
residual lag-1 correlation and weak sensitivity to existing priors do not establish robustness to
an omitted time-dependent bias basis.

The sensor-bias candidate below tests this missing degree of freedom. Its prior scale cannot be
justified by fitting this one failure. No gate based on whether a model was rejected has been
added, and no production decision rule has been changed to hide the result.

### Time-varying sensor-bias candidate

Inference policy **inference-2** adds `bias_model="dynamic"`, selected in research with
`--bias-model dynamic`. Production continues to use constant residual bias. The new component
is a continuous piecewise-linear curve for each physical sensor axis, with 900-second knots by
default. It is shared across course segments, GNSS gaps and mount epochs: a mount turn rotates
the physical signal relative to the sensor, but does not rotate the sensor's own bias curve.
Vertical-only fits project the same three-axis curve onto each bin's down direction.

The drift component is anchored to zero at the first retained time to remove its constant-level
ambiguity with the existing residual offsets. Those offsets, their calibration-derived priors
and their gravity-orientation dependence remain in the fit. Successive bias-knot increments
(in °/h) have independent Gaussian priors with variance `sigma_rw² × elapsed_hours` per axis.
This is a random-walk regularization of the curve, not a claim that hardware bias has this law.
The default `sigma_rw = 3 (°/h)/sqrt(hour)` is explicitly an unvalidated research assumption;
it was specified before this candidate's pilot and not selected to achieve a target p-value.

`--bias-knot-seconds` and `--bias-rw-sigma-dph-sqrth` accept lists for matched sensitivity campaigns.
All free, fixed-model, local-bootstrap and nonlinear-bootstrap fits include the same bias basis
and penalty. The preliminary free fit estimates observation weights, which are then frozen.
Joint covariance includes the bias coefficients. The existing identifiability calculation now
includes their columns, and the prior-sensitivity check widens their random-walk scale threefold
under the `bias_drift` key. Results record knot times, estimated drift, drift uncertainty, prior
scale, frame and inference-policy provenance. Old frozen manifests require a new review after
this scientific source/policy change.

[The four-fit development pilot](sensor-bias-pilot-060.json) used the same preserved still-globe
control and failure inputs, dynamic crab, axis-by-segment weights, forward-angle uncertainty,
and zero bootstrap replicates. All four fits converged in 37.25 seconds total:

| Scenario | Bias model | True-model p (diagnostic) | Curvature nuisance likeness | Gates |
|---|---|---:|---:|---|
| crab drift only | constant | 0.4324 | 0.8671 | pass |
| crab drift only | dynamic | 0.7224 | 0.9974 | excluded |
| crab + long sensor drift | constant | 0.0000291 | 0.6683 | pass |
| crab + long sensor drift | dynamic | 0.02374 | 0.9852 | excluded |

Both dynamic-bias fits cross the existing 0.95 curvature-identifiability limit; that limit was
not changed. On the failure fixture the analytic curvature standard error grows from 0.0866
to 0.1976. The true model is no longer rejected at 0.0027, but its fitted curvature moves from
0.8080 to 0.7089 rather than toward the true value 1. The candidate exposes uncertainty and
confounding; it does **not** demonstrate improved coefficient accuracy or retained measurement
power. It also excludes the clean sensor-drift control, so there is a real cost in eligibility.

These four reused development inputs/settings are a functional comparison, not independent
coverage or tail validation. No full-size nonlinear bootstrap or broad seed/prior/knot campaign
was run for this candidate. Before promotion, assess bias-prior and knot sensitivity, varied
turn timing/geometry, accepted fractions and conditional false rejection on independent campaigns.
Small tests cover body-frame continuity and projection, random-walk units/time scaling,
independent Gaussian MAP/covariance references, combined Jacobians, frozen weights, both bootstrap
paths, the tight-prior limit and research CLI forwarding.

Verified on 2026-10-04 with the pinned Python 3.14 dependencies and JDK 21:
130 analysis tests, 12 server tests and 14 Android unit tests passed; `lintDebug` and
`assembleDebug` passed. Server tests required execution outside the sandbox because its
cross-thread asyncio calls stalled. The final analysis suite took about six minutes.

`pytest analysis/tests/test_release060.py analysis/tests/test_policy.py` exercises short/dense GNSS,
identical/conflicting timestamps, missing-turn integration at 20/100 Hz, heading permutations,
free/fixed nonlinear MAP reference solutions with nonzero crab and 5°/15° priors, nonconvergence,
direct and seeded Gaussian covariance propagation, empirical bootstrap covariance and migration.
Android unit tests cover delayed recovery and stop cancellation, deterministic packaging, pending
upload identity, retry retention and terminal cleanup without losing acknowledgement. Real process
death and Bluetooth recovery on both physical IMUs remain part of BENCH_TECHNICAL.md.

## Seeded experiments

The opt-in `analysis/tests/research.py` harness records the software, policy, environment, seed,
scenario, sampling method, block length, per-run failures and runtime. The synthetic sensor's
rotation is differentiated from its attitude matrices; the fitting correction is not used to
generate dynamic crab. Constant per-leg crab inputs remain supported.

```sh
PYTHONPATH=analysis:server python analysis/tests/research.py --scenario drift+1 --truth all --seeds 1 --sampling moving --blocks 15 --bootstrap 20 -o docs/pilot-060.json
PYTHONPATH=analysis:server python analysis/tests/research.py --scenario pool --truth all --seeds 1 --units 2 3 5 10 -o docs/pool-pilot-060.json
```

Estimate larger campaigns from the pilot wall time and obtain approval before running them.
`--scenario all --truth all` covers within-leg crab 0, ±0.5, ±1, ±2, ±5°/h, smooth shifts,
finite-duration transitions, anisotropic/correlated gyro noise, routes at different latitudes,
dateline crossings, turn dropouts, thermal ramps, long-period bias and combined hardware faults.
Repeat with `--variant ble` as well as `spp`. `--sampling moving segment --blocks 5 15 30` compares
current moving blocks with experimental blocks restricted to contiguous segments. Exports include
empirical and current joint covariance, their eigenvalues and joint 95% coverage. Empirical
bootstrap covariance never replaces the production matrix automatically. Production bootstrap
refits use the local linearization, with a prior on the total crab angle; the nonlinear research
candidate above refits the complete geometry.

Results stay separate by truth, scenario, sampling and block length. Each group reports attempted
runs, analysis failures, eligibility exclusions, accepted runs, unconditional false rejection among
analyzed runs, rejection conditional on acceptance, and the complete gated decision rate among
attempts. Every binomial rate includes a Clopper–Pearson interval. Simulation explicitly assumes
approved provenance and a usable bench certificate; all remaining primary gates still apply.
It cannot establish actual physical provenance or hardware qualification.

Summary-level pooling uses known correlated unit effects, repeated observations per unit, unequal
covariances and varying unit counts. Closed-form independent univariate reference fixtures live in
`analysis/tests/pooling_reference.json`. These small checks are not tail calibration or a validation
of the general multivariate pooling approximation.

## Deterministic geometry stress domain

`--geometry stress` uses 288 named cells: latitude ±5°, ±35°, ±65°; two or six headings;
poor (20° total span) or good (120° for two headings, 300° for six) separation; 60 or 180
minutes; nominal speed 150 or 270 m/s; and zero, three or six deliberate turns. Nuisance and
sensor streams still vary independently by seed. Geometry-changing scenarios and turn overrides
are rejected in this mode. Speed is a design axis, not a claim of information strength: actual
worst contrast information and retention are reported from the design calculation.

List the cells without simulations, then select a bounded development subset:

```sh
~/venv/bin/python analysis/tests/research.py --list-geometry-cells -o /tmp/geometry-cells.json
```

`--geometry-cells ID ...` defines the preregistered domain. Summaries keep geometry cell and
test rank separate, including false rejection, model-separation power, information, exclusions
and denominators. Calibration takes the maximum threshold across the declared diagnostic
geometry/scenario cells for each operational rank. Every declared cell needs sufficient accepted
samples; permanently ineligible cells remain development evidence and must be excluded from the
claimed domain before freezing. The policy records the selected observable cell properties.
These are finite stress fixtures; they do not by themselves validate every intervening trajectory.

Use `--scenarios bias_mixed wind` to freeze an explicit nuisance subset, instead of a single
`--scenario` or the full `--scenario all` population. Duplicate names are removed. Explicit
protocols and stress cells reject geometry-changing members of an explicit subset.

### Fresh development screen, 2026-10-05

The implementation was committed as `f687734` before this screen. The approved ten-minute
compute budget produced [72 completed development evaluations](design-geometry-pilot-20261005.json)
across 25 geometry cells; another evaluation was interrupted at the cap. The initial two-cell
pilot varied all three truths, `bias_mixed` and `wind`, and dynamic/wind crab. Adaptive screening
then varied all six stress latitudes, 60-minute routes with zero/three/six turns, and 180-minute
routes with six turns, using six well-separated headings at 270 m/s. Sensor bias was dynamic;
all evaluations were design-only with zero bootstrap attempts.

[The summary](design-geometry-pilot-20261005-summary.json) records 64 analyzable evaluations
and eight analysis failures. None of the 64 passed any model-contrast design estimability test;
all had free-fit model-test rank zero at the frozen cutoff. The development cutoff sweep changed
rank for 21 of those evaluations; two were within the configured 10% boundary neighborhood.
These are seed-specific diagnostics, not population rates or independent tail evidence.

No eligible domain was found, so fresh flight/pairwise calibration and independent validation
were not run. Actual-flight pooling calibration likewise lacks informative inputs from this
screen. The next required step is a feasible geometry/protocol under the frozen nuisance gate,
followed by a complete-fit/bootstrap development pilot and reviewed campaign sizing before
freezing calibration. This bounded screen does not prove that all possible flight protocols,
or all 288 stress cells, are infeasible. Source/environment hashes are preserved in the records.

### Cruise qualification follow-up

The zero-rank screen exposed a preprocessing conflict: deliberate IMU turns split stable cruise,
and the ten-minute minimum was reapplied to each resulting fragment. Ten-minute turn spacing,
minus handling exclusions, therefore discarded otherwise useful alternating orientations.
`find_segments` now qualifies stable aircraft cruise before splitting it into averaging intervals
at deliberate IMU turns. Maneuvers, invalid/missing GNSS, placement shifts, disconnections and
unclassified exclusions still break qualification; bins never span handling windows or mount epochs.
The original screen remains a record of the earlier implementation, not evidence about this fix.

[Regenerated development trials](cruise-qualification-development-20261005.json) include the exact
[75-minute protocol](development-protocol-75min.json): bearings 10°, 100°, 190°, 280°, 10°, each
for 15 minutes, starting at 35° latitude and −30° longitude, speed 270 m/s, with sensor turns at
5, 15, 25, 35, 45 and 55 minutes. This trial cleared every design contrast and the duration gate
for both dynamic and wind crab when forward uncertainty was disabled. With measured forward-axis
uncertainty enabled, dynamic crab still cleared every design contrast; wind crab abstained.
These were design-only trials with no bootstrap evidence or empirical threshold claims.

Use `research.py --geometry fixed --protocol docs/development-protocol-75min.json` to reproduce
the selected geometry in fresh campaigns. The protocol content, geometry cell ID and domain are
frozen in the manifest; nuisance scenarios cannot override the trajectory or turn schedule.
The complete-fit/nonlinear-bootstrap pilot below supplies the next development evidence;
cost review and protocol/configuration freezing still precede independent calibration and validation.

### Complete-bootstrap pilot and proposed campaign, 2026-10-05

[Fresh paired development pilots](bootstrap-development-20261005.json) used seeds 600030–600032
for all three truths in `bias_mixed` and `wind`, with dynamic crab, dynamic sensor bias,
axis/segment weighting, measured forward uncertainty and 20 complete nonlinear bootstrap
replicates. **18/18 runs cleared eligibility and bootstrap convergence**, all at test rank 2.
A development cutoff sweep at 90%, 100% and 110% of the retention threshold found no rank
flips and no flights within 10% of the boundary. These are small development samples, not
tail validation. Full records and source/environment provenance are preserved in the
[compressed raw artifact](bootstrap-development-20261005.json.gz).

Repeated row construction and crab Jacobians now use batched coordinate calculations.
A matched flat-disc fit fell from 65.68 to 6.84 seconds; fitted coefficients changed by at
most 1.99e−14, with the same eligibility and rank. That repeated seed is timing evidence,
not an additional independent flight. The earlier flat-disc fit had rank 1, so the proposed
first campaign preregisters rank 2 only; other ranks abstain under its empirical rule.
The focused physical-mapping, Jacobian, gate and calibration checks passed 111 tests.
Python/NumPy/SciPy versions and the three declared numerical thread settings are frozen;
these pilots set all three thread counts to 1.

The [proposed calibration manifest](flight-calibration-proposed-manifest-20261005.json) restricts
the domain to this exact protocol, one candidate, rank 2 and the two tested nuisance scenarios.
It reserves threshold margin with calibration alpha 0.00135 and retains the claimed 0.0027
rate. The 18-test validation family includes the primary tests and pairwise endpoints.
Calibration requires 29,285 accepted flights per truth/scenario cell. Validation requires
33,169 per cell, allowing up to 64 false rejections for its exact bound; under the assumed
0.00135 rate, a union bound gives at least 95.23% family passing probability, exceeding the
requested 90% design power. That probability is conditional on the planning assumption.

At the pilot's 11.08 seconds per attempt and observed 100% acceptance, the minimum combined
compute estimate is **48 serial days**. Preregistering 35,000 calibration attempts and 40,000
validation attempts per truth/scenario cell reserves some acceptance loss and implies about
**58 serial days**. The validation manifest must be created after threshold estimation so it
freezes the actual primary and pairwise decision files. Actual acceptance under that rule
may be lower. Summary-level pairwise pooling needs a separate campaign and is not included
in these flight counts. The current per-record JSON rewrite should be replaced by checkpointed
batch output before a campaign this large. **No full calibration or validation campaign has run.**

### Bounded 1,000-flight development campaign

The bounded campaign covered 1,000 additional development attempts, about 3–3.5 hours, instead of the full
campaign above. `analysis/tests/development_campaign.py` interleaves fresh seeds 600100–600266
across the three truths and `bias_mixed`/`wind`, retaining all observed ranks. Each cell has
166 or 167 attempts. Settings match the complete-bootstrap pilot. Outcomes do not affect the
fixed attempt count; recorded analysis failures are retained and never retried to improve acceptance.

The worker freezes its own source/configuration/environment manifest and appends/fsyncs every
completed attempt to `docs/development-1000-20261005/records.jsonl`. Atomic `status.json` tracks
progress; `campaign.json` and `rank-sweep.json` are generated automatically on completion.
The detached worker needs no network or further model calls. It can survive chat disconnection
while its host remains running; after process/host interruption, resume uses durable checkpoints.
The process lock prevents duplicate workers. Changed source/environment/configuration prevents
resume, and source changes during a run stop it. A partial final write is preserved before repair;
complete malformed records are rejected. See [AGENTS.md](../AGENTS.md#analysis-campaign-handoff--2026-10-05)
for the fresh-chat handoff and remaining research order.

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ~/venv/bin/python analysis/tests/development_campaign.py --detach
```

For an interrupted campaign, repeat with `--resume --detach`. This is development evidence;
the six cells share paired seeds, and about 166 observations per cell cannot establish the
planned 0.0027 conditional false-rejection bound. Threshold calibration and independent
validation remain unfunded by this smaller authorization.

### Completed development results, 2026-10-06

The [1,000-flight campaign](development-1000-20261005/campaign.json.gz) finished in **3h16m**
(11.73 seconds per attempt). All attempts are checkpointed; there were **zero analysis
failures**, valid bootstrap convergence in **1,000/1,000** fits, and **906 eligible flights**.
The six cells use paired development seeds, so aggregated counts are descriptive rather than
1,000 independent observations from one null distribution.
The full campaign and append-only checkpoints are published as lossless `.gz` archives;
the worker uses their unpacked counterparts locally. Archive extraction instructions are in
the campaign handoff.

| Truth | Scenario | Attempts | Eligible | Eligible rank 2 | Eligible null rejections | Correct primary separation |
|---|---|---:|---:|---:|---:|---:|
| rotating globe | mixed bias | 167 | 166 | 166 | 1 | 165 |
| rotating globe | wind | 167 | 137 | 137 | 0 | 137 |
| still globe | mixed bias | 167 | 166 | 166 | 0 | 166 |
| still globe | wind | 167 | 138 | 135 | 0 | 138 |
| flat disc | mixed bias | 166 | 164 | 151 | 0 | 152 |
| flat disc | wind | 166 | 135 | 122 | 0 | 124 |

Correct primary separation requires retaining the generating model and rejecting both
alternatives among eligible flights. These decisions use the uncalibrated diagnostic rule.
The one eligible null rejection was in the rotating-globe/mixed-bias cell: 1/166 (0.60%).
Its illustrative simultaneous one-sided 95% upper bound with an 18-test family is 4.77%,
far above 0.27%. Neither that event nor the zero-event cells establish the intended tail rate.
Fresh threshold calibration and independent validation remain necessary.

There were 927 rank-2 and 73 rank-1 fits, including 877 eligible rank-2 fits.
The [default wide cutoff sweep](development-1000-20261005/rank-sweep.json) (0.5–1.5 times
the baseline) changed rank in 916 flights. The [narrow ±10% sweep](development-1000-20261005/rank-sweep-narrow.json)
changed rank in **47 flights**, all within 10% of the current cutoff. This supersedes the
small pilot's zero observed near-boundary cases and warrants development review of a rank
stability restriction before freezing calibration. No cutoff or eligibility policy was changed.

The 94 excluded flights had overlapping reasons: 91 failed the design-contrast gate,
16 depended on the WMM slip exclusion, and one was prior-dominated. Wind acceptance was
about 81–83%, versus about 99% in mixed bias; the exact geometry still needs review under
wind. Partial pairwise diagnostics produced 880 three-model winners, all matching their
generating model, and 120 abstentions. These were uncalibrated flight decisions; pooled
calibration/validation was not part of this campaign.

Using the worst observed eligible rank-2 fraction, 122/166, to plan equal attempt counts
across cells gives 39,847 calibration and 45,132 validation attempts per cell for the current
accepted-sample goals: **509,874 combined attempts, approximately 69 serial days** at the
measured runtime. This is an estimate, not a guarantee; acceptance under calibrated gates
may differ. The historical proposed 35,000/40,000 attempt reserves are insufficient at this
observed acceptance and must be revised before any launch. The next step is development
review of geometry/rank stability, then a fresh frozen plan and separately authorized budget.
No thresholds were estimated, no independent validation ran, and no primary policy was promoted.

### Selection review from saved records, 2026-10-06

The completed development work was published in commit `dd8575f`. A subsequent
[saved-record review](development-1000-20261005/selection-review-20261006.json) uses the same
shared scientific gate to evaluate hypothetical rank-margin settings. It does not refit,
change singular-value cutoffs, estimate thresholds, or alter the original campaign.

| Minimum relative rank margin | Eligible flights | Eligible rank 2 | Eligible null rejections | Estimated full campaign days |
|---|---:|---:|---:|---:|
| 0% (recorded rule) | 906 | 877 | 1 | 69.2 |
| 5% | 897 | 873 | 1 | 69.2 |
| 10% | 894 | 870 | 1 | 69.8 |
| 20% | 866 | 846 | 1 | 76.5 |

Costs use the worst observed eligible rank-2 fraction in a truth/scenario cell; they are
point estimates, not guaranteed budgets. The 10% margin costs 12 currently eligible flights
and does not remove the observed null rejection. It remains a development proposal rather
than an adopted eligibility policy or a substitute for calibration.

All 91 design-contrast failures coincide with a magnetic-watchdog slip flag: 88 in wind and
3 in mixed bias. The watchdog flagged 132/500 wind and 6/500 mixed-bias flights even though
the saved simulator configurations specify zero mount creep. The current watchdog compares
magnetic direction with GNSS course and WMM declination; it includes no wind-crab heading
term. Confounding aircraft-heading change with mount motion is therefore a concrete
hypothesis to test. These records lack the per-segment watchdog output and rejected-bin
geometry needed to establish the causal effect. The next development diagnostic should
retain those quantities and compare wind with genuine mount slip, preserving the protective
gate while testing specificity. No further flights were authorized or run for this review.

Reproduce the report from the published archive:

```sh
env PYTHONPATH=analysis:server OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ~/venv/bin/python analysis/tests/review_development.py docs/development-1000-20261005/campaign.json.gz -o /tmp/selection-review.json
```

### Magnetic watchdog diagnostic and next pilot, 2026-10-06

The bounded campaign covered the [eight-case plan](development-1000-20261005/watchdog-diagnostic-plan-20261006.json).
All eight paired development replays completed in **52.05 seconds**, with zero bootstrap
replicates and geometry-only fitting. The [complete diagnostic](development-1000-20261005/watchdog-diagnostic-20261006.json)
preserves magnetic bins, both watchdog variants, simulator settings and before/after selection
geometry. These are replays and counterfactual mount-creep controls, never new independent evidence.

At rotating-globe/wind seed 600107, zero injected mount creep still flagged segments 0 and 6
at apparent rates +1.605 and −2.027°/h. Selection removed nine of 74 bins and lowered the
minimum design contrast retention from 0.394 to 0.196, below the 0.31225 threshold.
The [saved-bin oracle review](development-1000-20261005/watchdog-review-20261006.json) supplies
the simulator's known wind to the heading reference: it removes those false flags while retaining
slip detections in every 3°/h positive control. All four zero-creep cases then have no exclusions.
This establishes crab confounding in these cases, rather than its population-wide frequency.

The oracle is a diagnostic, not an operational correction: independent aircraft heading or a
validated wind/airspeed estimator is unavailable to the present watchdog. With zero airframe
field, changing crab and mount yaw can produce identical magnetic signals. `magnetic-watchdog-2`
therefore describes an **apparent yaw change**, reports `mount_slip_confirmed=false`, and
retains conservative exclusions. Legacy fields and flags remain for compatibility; analysis also
emits `magnetic_yaw_change_ambiguous`. Research records now retain the full watchdog output
and pre-exclusion geometry, including failed attempts, so future reviews need fewer replays.
The WMM sensitivity check and eligibility criteria continue to account for selection.

The next authorized development pilot has **exactly 1,000 attempts**, paired seeds 600300–600466,
the same three truths and `bias_mixed`/`wind` scenarios, full 20-replicate nonlinear bootstrap,
and a preregistered 10% relative rank-boundary margin. All observed ranks are recorded; the
proposed calibration domain covers rank 2 only. It makes no guarantee for other routes, latitudes,
sensor variants, nuisance scenarios, or pooled pairwise summaries. A broader flight domain still
requires the deterministic geometry stress matrix and separate calibration/validation.

The documented corpus is `development-1000-20261006/`: `manifest.json`, fsynced
`records.jsonl`, atomic `status.json`, worker launch/log/lock, and automatic `campaign.json`,
`rank-sweep.json`, `rank-sweep-narrow.json`, `magnetic-summary.json`, and compressed campaign/journal
archives. Freeze all scientific code and numerical thread settings while the worker runs.
See [AGENTS.md](../AGENTS.md) for the exact launch/resume command and authorization.

The [refreshed calibration proposal](flight-calibration-proposed-manifest-20261006.json)
freezes current source/environment, rank 2, the 10% margin, and primary plus separate pairwise
endpoints. Cost estimates now apply the proposed rank margin to historical pilot records:
241,062 calibration attempts plus 273,030 validation attempts, **514,092 total / about 70 serial days**.
Sample goals remain 29,285 accepted calibration and 33,169 accepted validation flights per
truth/scenario cell, calibration alpha 0.00135 and claimed alpha 0.0027, with an 18-test family.
The draft calibration reserve is 45,000 attempts per cell; a matching future validation reserve
would be 51,000 per cell (576,000 combined / about 78 days at the historical runtime).
These are planning estimates, not guaranteed acceptance or an approved compute budget.

After the fresh pilot finishes, review its rank, selection, convergence and separation results,
refresh costs and freeze the final method before seeking full-campaign authorization. Run fresh
calibration next, freeze actual primary and pairwise threshold files, then freeze independent
validation using those files. A validation manifest cannot yet be finalized without the thresholds.
The old proposed manifest and old development evidence retain their original source hashes.

### Completed second development pilot, 2026-10-06

The fresh-seed pilot is complete: 1,000 attempts in approximately 3h24m, zero analysis failures,
905 eligible flights (884 rank 2), and zero eligible diagnostic generating-model rejections.
[The complete report](development-1000-20261006/README.md) separates the six truth/scenario
cells, ranks, selection, bootstrap validity, model separation and pairwise outcomes.
The full campaign and completed journal are saved as lossless `.json.gz`/`.jsonl.gz` archives.
The worker must not be resumed or its attempts rerun.

Ranks were 936 rank 2, 62 rank 1 and two rank 0. Bootstrap validity was 998/1,000; both invalid
fits were still-globe/wind rank-0 records and were excluded. Overlapping exclusions were 72
design-contrast failures, 53 rank-margin failures, 11 WMM-selection failures, two unavailable
subspaces and two inadequate bootstraps. The ±10% cutoff sweep changes rank in 53 flights;
none is eligible. The wide sensitivity sweep changes rank in 942 flights.

The watchdog flags 120/500 wind and 3/500 mixed-bias attempts with zero injected mount creep.
All 72 design failures coincide with those flags (69 wind, three mixed bias), confirming that
selection remains a material limitation. This association does not identify mount motion as
the cause; apparent yaw/crab confounding and conservative exclusions remain part of the method.

Primary diagnostic separation is 888/905 eligible flights. Pairwise decisions/abstentions are
922/78 (rotating versus still globe), 626/374 (rotating globe versus disc), and 887/113 (still
globe versus disc). Pairwise three-model winners are 888 correct, zero incorrect and 112
abstentions. These are uncalibrated development diagnostics from paired seeds, not validated
false-rejection or power estimates.

At worst observed eligible rank-2 acceptance 128/166 and 12.26 seconds per attempt, the existing
sample goals imply 485,976 combined calibration/validation attempts, about 69 serial days before
reserve. Refresh the frozen proposal and obtain a new budget before launching anything.
Fresh calibration and separate pairwise thresholds must still precede a frozen independent
validation campaign. No thresholds or production policy were promoted by this pilot.

### Next-stage preparation and revised freeze, 2026-10-06

[Preparation artifacts](research-next-stage-20261006/README.md) compare both completed pilots
using saved inputs and the shared 10% margin. Eligible counts are 894 and 905, including 870
and 884 rank-2 flights. The first pilot's one eligible diagnostic null rejection remains;
source versions/candidates are kept separate and never pooled into an empirical decision rule.
Wind/watchdog selection persists; no protective exclusions or outcome-dependent gates are relaxed.

The prospective geometry plan contains 24 deterministic cells covering the stress-matrix factors
and poor-heading/no-turn interactions, plus five observed-track windows and two explicitly
coverage-blocked tracks. Every full-matrix schedule meets the ten-minute spacing/five-minute
edge rule after correcting the former eight-minute spacing in 60-minute/six-turn cases.
The subsequently authorized synthetic diagnostic completed as described below. Observed-trajectory
replay still requires integration and checked simulated mount/sensor/nuisance assumptions.

The [restricted calibration proposal](research-next-stage-20261006/calibration-proposed-manifest.json)
is frozen to the current source/configuration/policy/environment, retaining exact 75-minute
geometry, SPP, rank 2, the 10% margin, both nuisance scenarios and primary/separate pairwise
endpoints. The old proposal retains its historical freeze and must not be launched with the
new source. Real-flight, external-GNSS and pooled-summary domains remain outside this proposal.

Sample goals remain 29,285 accepted calibration and 33,169 accepted validation samples per
truth/scenario cell. The latest point estimate is 485,976 attempts / 69 days. A conditional
reserve using simultaneous acceptance bounds and negative-binomial attempt caps is 560,670
attempts / 80 days: 43,830 calibration and 49,615 validation attempts per cell. Planning error
is split between acceptance bounds and attempt caps; this assumes stable independent within-cell
acceptance and does not bound runtime or future calibrated-rule acceptance.

The later one-hour synthetic geometry batch is complete; no further compute is authorized.
Geometry review precedes final envelope approval;
source changes require another freeze. Fresh calibration must generate actual primary/pairwise
threshold files before independent validation can be frozen. Real IMU bench work awaits hardware.

### Completed 300-case geometry diagnostic, 2026-10-06

[Results and verified archives](geometry-development-20261006/README.md) preserve 300 evaluations:
24 stress cells plus exact-protocol controls × three truths × two scenarios × dynamic/wind crab
fits. All use shared fresh development seed 600500, zero bootstrap and the frozen one-thread
environment. Runtime was 1,838.56 charged seconds (30m39s), below the one-hour cap.
Six no-fit results are retained, all mixed-bias cases at -65°, two poorly separated headings,
180 minutes, 270 m/s and no turns. All other returned fits reported convergence.

Zero of 25 geometries passes all intended contrasts across every candidate nuisance fit.
The exact protocol passes 6/6 dynamic-crab cases but 0/6 wind-crab cases, where the limiting
contrast is still globe versus disc. Worst control retention margins are +0.08401 and -0.31137
respectively. Dynamic/wind fits have 133/130 rank-zero results across the complete batch.
This development finding needs inspection of wind tangent/anchor assumptions and stress-cell
rank loss before new geometry or calibration; it is not proof that all feasible schedules fail.
The existing restricted dynamic-crab proposal does not cover the broader nuisance-model set.
No empirical thresholds, calibrated power, independent tail bound or real-flight guarantee
follow from a one-seed geometry diagnostic. Future numerical work may use up to two threads,
with a new environment freeze and measured cost; completed evidence keeps its original freeze.

### Geometry audit and revised protocol comparison, 2026-10-06

[The audit](geometry-development-20261006/audit.json) uses saved records and small analytic
bin fixtures, with no synthesized flight or nonlinear solve. It identified parameter-unit
dependence in numerical nuisance-rank selection: weighted nuisance columns are now normalized
before SVD. Extreme-scale and zero-column regression checks preserve the same nuisance span.
Science cutoff, unpenalized projection, anchor assumptions and protective gates are unchanged.
New contrast reports expose pre-cutoff information/retention separately from retained values.
This numerical fix changes the implementation hash; historical results keep their original freeze.

The stress matrix's nominal six-heading/60-minute cells give each leg exactly ten minutes,
equal to the stable-cruise minimum. Turn smoothing excludes intermediate headings: the +35°
case retains two headings and 25 bins even without watchdog exclusions. The 180-minute analytic
fixture remains rank zero until dynamic-bias columns are removed diagnostically; longer dwell
can let bias absorb slow science signals. All six actual no-fit records carry watchdog/no-bins
flags. These effects do not justify removing bias or watchdog gates.

All six wind-control cases, and one stress case, change worst-anchor rank under a ±10% science
cutoff shift. Wind-angle/rate Jacobians pass finite differences at all three physical anchors;
the extra course-modulated nuisance coefficients can remove information. Analytic ablations
support an interaction among crab, bias and forward uncertainty; they do not reconstruct the
historical Jacobians or establish that column scaling caused those recorded failures.
Design anchoring excludes fitted gyro science coefficients/weights, while retained bins and
measured forward/mount axes still condition the calculation. That caveat is explicit in reports.

The bounded campaign covered [72 fresh geometry evaluations](protocol-development-20261006/README.md):
three paired development seeds 600501–600503, old protocol versus nominal 90-minute repeated
opposing headings, three truths, two scenarios and both crab models. The candidate uses 15-minute
legs and six spaced mount turns; its ideal tangent fixture passes every anchor/crab contrast.
The completed batch tested actual cruise/attitude/watchdog processing: 72/72 evaluations,
zero fit failures, all fits converged, 516.91 charged seconds (8m37s). It used zero bootstrap,
two numerical threads and a 15-minute cumulative cap. Source hash is
`27e73b122c3a073357d4a03112da11779969a710bb3a6cc3eb06c333da52ad51`;
the old calibration proposal is stale and needs final-domain review and a new environment freeze.

| Protocol / crab fit | All design contrasts estimable | Scientific screen passes | Model-test ranks |
|---|---:|---:|---|
| Original / dynamic | 18/18 | 18/18 | 18 rank 2 |
| Original / wind | 9/18 | 6/18 | 15 rank 2, 3 rank 1 |
| Revised 90-minute / dynamic | 0/18 | 0/18 | 18 rank 2 |
| Revised 90-minute / wind | 0/18 | 0/18 | 12 rank 2, 6 rank 1 |

Neither protocol passes all 36 preregistered comparisons. The original/revised worst
estimability margins are -0.311505/-0.307931. Rank-instability exclusions affect 6 original
wind, 13 revised dynamic and 10 revised wind cases; exclusions overlap design failures.
All model decisions abstain. These screens do not establish prior sensitivity, calibrated
power or a tail bound. The revised IMU turn at minute 20 overlaps the first simulated aircraft
turn; its causal effect has not been isolated. The ideal fixture's positive retention margin
therefore did not establish adequacy through the complete processing chain.

The completed review verifies the source/environment/runner/input freeze, task identities,
lossless compressed journal and recomputed scores. Next use saved processing diagnostics and
independently checked trajectory/attitude fixtures before selecting a new protocol. No extra
cases or corrective reruns are authorized by the remaining time; do not resume completed batches.

### Saved-processing and independent attitude audit

The later [processing review](protocol-development-20261006/PROCESSING_REVIEW.md) uses saved
diagnostics and independent component fixtures, with no additional flights or nonlinear fits.
Before/after-cutoff all-contrast passes are original/dynamic 18/18→18/18, original/wind
14/18→9/18, revised/dynamic 18/18→0/18 and revised/wind 0/18→0/18. There are no watchdog
exclusions in these 72 cases. Independent aircraft/IMU-turn overlaps cause mount-mapping
errors of 14.85° (constant aircraft yaw) and 7.46° (coordinated bank); no gap flag detects the
motion confounding. This isolates a mechanism, not its contribution in the historical campaign.
The unrun 5/25/40/55/70/80-minute proposal avoids known overlap and passes coarse known-axis
contrasts, but has a narrow 0.3274 minimum retention and no demonstrated full-pipeline acceptance.
Raw sessions, bins and mount matrices must be retained in a later budgeted comparison.

## Experimental partial pairwise evidence

The versioned derived shape rule `globe-disc-pair-rule-1` emits `shape_evidence` in candidate
fits, final session analysis, research records and pairwise pools. It ignores the rotating-versus-
stationary-globe comparison. At least one eligible, internally consistent globe-versus-disc
preference supports the globe family; disc requires both comparisons to prefer disc. Opposing
preferences cause abstention. Neither/both endpoint rejections alone supply no preference.
All contributing pair-specific gates and calibration-domain restrictions remain in force.
This is evidence about the two implemented globes versus the implemented stationary disc.

The family rule is experimental even when its contributing pair thresholds are calibrated.
`pairwise_thresholds_calibrated` describes only those inputs; `error_rate_validated` and
`validated_for_primary_claims` remain false. Under disc truth, choosing either globe comparison
can accumulate false rejections. An endpoint bound is not a same-sized family bound, especially
with different data-dependent eligibility sets. Preregister the composite rule/error budget and
validate wrong-shape outcomes under all three truths, retaining failures and abstentions.
Existing endpoint assessments do not certify this new conclusion.

The geometry optimizer's `--objective globe-disc` requires both untruncated pair contrasts to
survive the same nuisance envelope, without requiring globe-rotation separation or global
science rank. `--comparison` still permits a single pair design. A full three-model objective
remains the default; shape and single-pair objectives are explicit alternatives, not relaxed
three-model qualification.

`analysis/tests/review_shape_evidence.py` derives preferences solely from preserved decisions
in the two development campaigns. Results in `research-next-stage-20261006/shape-review.json`
bind original input hashes/freezes and the current rule. Counts are 889/0/111 and 900/0/100
correct/incorrect/abstaining, with 9 and 12 additional shape preferences beyond recorded
three-model winners. These historical observable-coordinate fits are not fresh direct profiles,
current airline replay, calibration or independent validation.

The subsequent fixed nominal direction screen, `research-next-stage-20261006/route-direction-screen.json`,
contains 21 route/pattern controls: 12 safe, 24 candidate evaluations, two preserved no-bin
failures, in0.542s. Five prepared75-minute paths plus the extended120-minute path are compared
with its counterfactual reverse. With six distributed turns, the reversed physical-wind case
has shape pre-cutoff retentions0.415376/0.436039 and rotation retention0.298360,85 analytic
minutes and adequate headings. Original westbound shape retentions are0.124577/0.305099.
Broader wind fails the reversed shape contrasts at0.253845/0.293767. No case passes both shape
contrasts across both candidates. The physical-wind SEA–KEF nominal pass at0.333473/0.415521
fails observable qualification at55 minutes and inadequate headings. These are nominal
zero-nuisance controls, not complete envelopes, full preprocessing or power. Two reversal
controls passed0.39s; no new simulated flight, analysis refit or empirical threshold ran.

The [airborne-source inspection](research-next-stage-20261006/AIRBORNE_DATA.md) preserves four
public catalog responses and `airborne-catalog-review.json`, generated offline by
`analysis/tests/review_airborne_sources.py`. ILVIS0 current collectionC3162704221-NSIDC_CPRD,
DOI10.5067/E6JPQ3QNW77R, has actualgyro file candidates. A64KB range probe returned302 to
Earthdata login with0 measurement bytes. The supplied C1386246599-NSIDCV0 identifies distinct
IPUTI0, DOI10.5067/7K31MCH5XXZA; its directory also redirects to login. IPUTI0 metadata advertises
ASCII position/velocity/orientation, not confirmed independent gyro columns. The2014 Applanix
V6 ICD documents packets but leaves IMU payload formats unpublished; its applicability to the
2009 log is unverified. The user has since registered and supplied an IPUTI0 binary sample,
clock file and three format descriptions. `analysis/tests/inspect_iputi0_sample.py` preserves
these in `research-next-stage-20261006/airborne-sample-iputi0/inputs/` with SHA256 provenance,
and produces an exploratory navigation CSV and inspection record. The binary interleaves
3500 system status and3501 navigation solution: position, velocity, pitch, roll and heading,
with no independent gyro rate/increment fields. Signed fixed-point decoding follows the
supplied scaling; little-endian word/checksum conventions are inferred from observed data.
There are1,527 verified packets of each type. A checksum-failed candidate at offset10,800
overlaps valid frames recovered11bytes later;11unframed bytes are preserved, not repaired.
The clock's relative span is1,525.99469s at approximately1Hz; timezone, binary time-tag
representation/epoch/alignment and status-bit semantics remain unresolved. Horizontal
speed69.51–93.69m/s is consistent with airborne motion. Three focused decoder checks pass0.02s.
No navigation-rate substitution, credential inspection, full-pipeline fit or empirical
discriminator result exists. The subsequent ILVIS0 log now provides a time-tagged IMU stream,
but physical payload decoding remains unresolved. Offline `analysis/tests/inspect_ilvis0_sample.py`
preserves the13,086,748-byte original and produces the explicitly documented
`research-next-stage-20261006/airborne-sample-ilvis0/` corpus with opaque timed IMU payloads,
fused navigation, reconstructed primary GPS and hashes. All143,471 outer frames pass the
documented whole-frame16bit checksum (including endmarker); no repair/resync is performed.
132,444 Group4 IMU8 packets span662.2256497321068s at approximately200Hz, no gaps>7.5ms.
Headerdata/status0; AV-510 VER5 firmware04.60/ICD15.00/IMU8 identifies exact format target.
The2014 V6 ICD is compatible with observed containers but not verified for every2009 field.
Payload24bytes remains opaque: scaling, axis order, increments/rates and corrections unknown.
Group10002 is absent.662 Group1 fused navigation packets must not replace independent gyro.
Reassembling5934 Group10001 GPSframes recovers660 checksum-valid GGA,660 VTG and660 ZDA;
all GGA fix-quality1, ZDA date2009-04-14.10GGA markers span frame boundaries. Compatible
timebyte2 denotes UTCtime1/POSsincepowerontime2; latency/leverarms still unverified. Track
79.72N→78.86N over Greenland, navaltitude~6.9→7.5km and rollmin−17.5deg indicate climb and
maneuvers, not a qualified entirelevelwindow. Two focused checks pass0.02s. No physicalgyro
decoder, mainpipelineimport, calibration, empiricaldiscrimination or WT901claim. A precise
IMU8documentation-request draft is saved in AIRBORNE_DATA; no external message was sent.

The subsequent bounded design check runs at most30 SVDs, not simulated flights:
`analysis/tests/check_direction_counterexamples.py` records exact registered physical-wind
states at reference TAS on the reversed120-minute path/sixsafe turns. All30 tested states
retain both globe/disc contrasts, minimum fractions0.403480/0.431011 versus0.312250;
elapsed0.100963s. The cap stops mid-grid, so no complete-envelope pass is established.
Broadwind already fails nominal; no fullpipeline/power result or protocol promotion follows.
`research-next-stage-20261006/PLAN_STATUS.md` maps implementation versus outstanding evidence.

Candidate fits emit `pairwise` entries for all three comparisons. Each applies the shared gates
with only that comparison's design retention required. The free-fit retained science space defines
an observable scalar normalized to first model=1 and second model=0, with covariance propagated
from the joint fit. An unavailable coordinate, invalid bootstrap or failed gate abstains. A preference
requires rejecting one endpoint while retaining the other; two retained or two rejected endpoints
also abstain. A three-model winner requires preferences against both alternatives.

Pairwise diagnostics use six-endpoint Bonferroni tests and remain experimental. Enable
`--pairwise-evidence` when freezing a campaign to preregister the additional validation family.
It selects the candidate engine, and records per-pair eligibility, rejection, power and abstention
even for flights excluded from the full three-way gate. Calibrate the pairwise rule separately:

```sh
~/venv/bin/python -m lll.pairwise_calibration calibrate calibration.json --mode flight -o pairwise-decision.json
```

Use `--pairwise-decision-policy pairwise-decision.json` in the frozen independent validation
command, then assess it separately:

```sh
~/venv/bin/python -m lll.pairwise_calibration assess validation.json --policy pairwise-decision.json -o pairwise-assessment.json
```

Collation emits `experimental_pairwise` alongside the existing primary result. It pools only
flights eligible for each comparison, first within physical IMU units, then across units using
REML and modified Hartung–Knapp uncertainty. At least three informative units are required for
a pooled decision. Repeated flights never manufacture additional units. Pair-normalized coordinates
let different retained science projections share the same two null endpoints.

Pooled decisions have their own `--mode pool` calibration artifact, keyed additionally by pair
and informative unit count; a flight policy cannot calibrate a pool, and uncalibrated unit counts
abstain. `lll collate --pairwise-decision-policy FILE` applies such an artifact. Summary-level
pooling campaigns use `--scenario pool --pairwise-evidence --units 3 5 10`; they exercise the
known-unit-effects generator, not the flight geometry/nuisance pipeline. Their candidate identity
prevents transferring those thresholds to pools of actual flight analyses. Actual-flight pooled
campaigns require their own recorded pools, independent cohorts and calibration/assessment.
None of these artifacts promotes experimental candidates into primary observational claims.

## Hardware and publication sequence

### Small pilot, 0.6.0

[Flight pilot](pilot-060.json): one seed per truth at +1°/h within-leg crab, moving blocks of 15
bins and 20 bootstrap replicates. All three analyses converged and retained their true model;
all three were excluded by primary gates (prior sensitivity, and additionally WMM selection
sensitivity for the still globe). There are **zero accepted runs**, so this pilot says nothing
about accepted-flight false-rejection tails. Runtime was about 26 seconds on the recorded environment.

[Matched zero-crab baseline](baseline-060.json): the same seed, routes, sampling and bootstrap
settings also yielded three converged analyses, no true-model rejections and zero accepted flights.
All three were prior-dominated even without crab drift. The +1°/h run additionally triggered WMM
selection sensitivity for the still globe. Across coefficients, the largest changes from baseline
were 0.82, 0.49 and 0.36 baseline standard errors for the rotating globe, still globe and flat disc,
respectively. These paired changes are descriptive, not significance tests or evidence for accepted
flight coverage. The baseline took about 27 seconds.

[Baseline prior diagnostics](baseline-diagnostics-060.json) attribute the zero-crab exclusions
mainly to the residual-bias prior: widening it 3× moves the curvature estimate by 2.40σ, 1.98σ
and 2.18σ for rotating globe, still globe and flat disc, respectively. Widening the crab prior
also moves the rotating-globe rotation estimate by 1.72σ. These are within-fit sensitivity checks;
they do not estimate rejection rates.

The same seed and routes with three same-side-up IMU turns at 20, 50 and 80 flight minutes are in
[zero-drift turns](turn-zero-060.json) and [+1°/h drift turns](turn-drift-060.json). With turns,
the largest bias-prior shift falls below 0.01σ in every run. At zero drift the flat-disc flight
passes the scientific gates, while both globe flights remain prior-dominated by crab sensitivity
(largest shifts 1.12σ and 1.04σ). At +1°/h, the still globe and flat disc pass; the rotating globe
remains prior-dominated (largest crab-prior shift 1.24σ). All six retain their true model. These
six single-seed outcomes establish only that the turn-enabled fixture can produce accepted
flights; they do not calibrate false-rejection tails or justify changing the gates.

For a turn-enabled pilot, add `--same-side-up-turns` to the research command. Vary seeds, routes
and scenarios before choosing a larger campaign; the accepted fraction and scenario-specific
null outcomes should be reported with their denominators and binomial uncertainty. No stored
observational corpus existed at this checkpoint, so no reprocessing was needed.

[Pooling pilot](pool-pilot-060.json): one seed per truth at 2, 3, 5 and 10 units, with correlated
unit effects and unequal session covariance. No true-model rejections in these 12 summaries;
two-unit results are exploratory. This is a runtime/functional check, not a tail study.

Two historical regression assertions required the still-world fixtures to reject the rotating
globe. The corrected total-angle objective changes the fixed-model fits and conservative bootstrap
calibration enough that they no longer do so. Correctness tests retain true-model coverage, require
valid nested objectives and compare free/fixed MAP fits with an independent optimizer. Rejection
power must be reassessed using the harness; no noise floor or significance threshold was tuned to
restore those historical assertions.

## Observed-route partial envelope — 2026-10-07

The authorized single-control design check in
`research-next-stage-20261006/observed-pair-envelope-result.json` completed in29.7007s:
15,210unique registered states, one numerical thread, within the120-second cap. Frozen plan:
`observed-pair-envelope-plan.json` in that directory. Input is the actual ORD–LAX track,
elapsed3600–10800s, C2-interpolated assumed motion, IMU turns5/15/30/40/90min, physical
wind/TAS candidate and dynamic bias/forward uncertainty. The grid crosses65wind/TAS states,
3model anchors,3forward offsets,13nominal/individual-epoch mappings and2noise levels.

The target `sphere_still_vs_flat_still` passes the untruncated direct-pair design criterion:
retention0.3650996659622584, threshold0.31224989991991997, margin0.05284976604233843,
minimuminformation20.484201633970038. Worst-retention state is
`epoch-1-1/wind--1-0/tas-250.0/forward-0.261799388/sphere_still/noise-3/none`.
An independent rotation implementation reproduced that retention to1e-10. The global-cut
target retention0.3621652194879138 also passes. Global rank is1 in all15,210states.

The direct rotation contrast retains0.31461461894776643, narrowly passing; its global-cut
retention0.3120686256034943 fails. Rotating-globe/disc retains0.14419675836858453 directly
and0.12864914359234356 after the global cutoff, failing both. Thus this is partial design
evidence, not full three-model eligibility. Broad wind already fails this control nominally.
The finite physical-wind assumptions remain provisional; known design axes and assumed
interpolation do not establish recovered-axis or complete-pipeline performance.

Result/source/input/environment hashes were verified, all state IDs checked unique, and the
frozen plan is preserved. No noisy replay, fit, bootstrap, power, calibration or validated
Earth-model decision was performed. Next is separately budgeted matched full-pipeline replay
of this fixed control before any new calibration. The one-envelope allowance is complete.

## Observed-route replay and specific-force audit — 2026-10-07

The separately authorized six attempts (three truths × wind/wind_tas, shared seed600910,
wind+bias_mixed) completed with no processing failures and all fits converged. Corpus:
`observed-pair-replay-20261007/`. Wall335.204s; summed attempt time376.529s. All retained99
cruise minutes, six mount epochs and adequate headings. Paired fitter inputs match across
all23saved fields. Rank1 throughout; no watchdog exclusions. Rotation and stationary-globe/
disc pairs pass eligibility6/6; rotating-globe/disc0/6. No primary acceptance, bootstrap or
calibrated decision: every pair abstains. Target profileSD0.624–0.644, endpoints one unit apart.

`noise-review.json` reports preliminary residual-based weightingσ38.28–38.36dph against
planningσ3/6dph. `residual-decomposition.json` independently reconstructs the prescribed
C2 path, wind triangle, pitch/bank and tray turns with SciPy rotations; it evaluates saved
free parameters without invoking synthesis, SVD, fitting or bootstrap. Saved observation
rows and Jacobians are reproduced before attribution. Exact saved-bin half-open membership
and corrected clock timestamps determine the averages; nominal sample times are recovered
by rounding to the frozen20Hz grid. This assumes the replay's known clock origin and motion,
not real-flight truth access. Every input, scientific source and helper is hash-bound.

Let M be the prescribed body angular rate averaged over a retained minute, S the prescribed
inertial science rate in the IMU frame, Bcal the saved ground calibration, and Mfit the
pipeline motion correction including fitted crab rate. Decompose the saved final residual as

```text
motion error  = M − Mfit
science error = S − fitted science
sensor error  = (gyro − Bcal − M − S) − fitted residual bias/drift
final residual = motion error + science error + sensor error
```

Closure is below1e-7dph (observed near machine precision). The report preserves the complete
component second-moment matrix; correlated components cannot be added as independent
variances. Final residualRMS39.23–39.29dph differs from frozen preliminary weightingσ.
Motion mismatch is39.63dph; sensor/calibration remainder about3.9dph before fitted drift,
4.54–4.56dph after it; science/orientation mismatch1.08–1.13dph. Configured white-noise
averaging predicts about3.25dph/minute, with independent uniform quantization adding about
1.83dph descriptively; saved SEMs are about3.8–4.1dph. Correlated rounding is not guaranteed
to follow that estimate. These quantities characterize this simulated seed, not hardware.

The dominant issue is treating specific force as gravity. The simulator generates
`f_b = C_bn (a_n − g_n)`; processing uses `unit(f_b)` as up and subtracts
`cross(dup_dt, up)`. Changing translational acceleration can therefore create an apparent
tilt correction without the corresponding body rotation. The assumed specific-force
direction reproduces saved up within0.0035deg. Its difference from true gravity reaches
2.52deg, yielding false tilt correction38.12dph RMS. Actual prescribed roll contributes
8.41dph RMS, insufficient to explain the discrepancy. An independent fixed-orientation,
changing-acceleration fixture reproduces the false rate, with segment and bin tests (3pass).

Substituting prescribed true up in motion correction, while retaining saved fit parameters,
lowers residualRMS to about12dph; remaining motion mismatch is11.33dph. This is a diagnostic,
not a refit, acceptance change or deployable correction. Correct acceleration-aware gravity
and motion recovery must use observable position/IMU data with position derivative, wind,
orientation and gap uncertainty. It also needs to address averaging/differentiation of
remaining motion. No scientific source or frozen record changed, no flight attempts were
added, and no empirical threshold or power claim follows. This processing issue precedes
further noise-policy tuning or a calibration campaign.

## Observable acceleration-correction prototype — 2026-10-07

`analysis/tests/acceleration_motion.py` implements a versioned research-only specific-force
correction, outside the production analysis package. `review_acceleration_motion.py` first
constructs corrections from saved GPS, measured accelerometer magnitudes, recovered epoch
maps and forward direction. Only a separate posthoc block accesses prescribed motion/truth
for scoring. No synthesis, optimizer, bootstrap or decision is invoked. Scientific source
and the completed six-task replay remain unchanged. Corpus: `acceleration-motion-20261007/`.

Force and horizontal velocity/altitude use common Hann support, with acceleration from
local derivatives and vertical acceleration from the second altitude derivative. Frequent
GPS (nominal intervals≤2s) and complete IMU support are required. The iterative frame solve
uses `unit(f_b−C_bn a_n)` with the supplied forward/heading reference. The correction then
uses the antisymmetric part of `−dC_bn/dt C_bnᵀ` and integrates it over fully supported
minute intervals. Derivatives and filters never cross GPS gaps or unsupported mount turns.
The prototype does not add model-specific Coriolis/curvature accelerations.

Each case evaluates81states crossing15/30/60-second filters, crab offset−15/0/+15deg,
crab rate−3/0/+3dph and forward offset−3/0/+3reportedσ, plus12nominal30-second axial
±3marginal-σ acceleration/force controls. GPS speed/bearing/height accuracy and measured
force SEMs propagate through the linear Hann/derivative kernels under independent-error
assumptions. These marginal scales are not a temporal covariance, validated interval or
weight usable in a calibrated model test. Correlation, instrument systematics and a coupled
physical wind/forward model remain open.

All six saved cases complete all93states. Nominal support85minutes; common support83minutes.
On the identical85minutes, baseline final residualRMS33.75–33.89dph falls to11.12–11.20dph
when replacing motion while holding science/bias/crab parameters fixed. Prescribed-motion
error becomes10.05–10.12dph. On common83minutes, state residuals span9.64–37.28dph;
no favorable state is selected or promoted. Eleven focused checks pass, including an
independent combined Euler-rate fixture, no-body-rotation acceleration, real roll, filter
uncertainty propagation and gaps/out-of-envelope support. Report, inputs, arrays and source
dependencies are hash-checked in `support-corrected/verification.json`.

The initial preserved run rejected six uncertainty states globally when a few samples
crossed the existing1.5m/s² acceleration limit. Local support handling now excludes those
samples and every minute touching their invalid derivative support. The limit is unchanged.
That initial report and its exact prototype source snapshot are retained; the current report
is in `support-corrected/`. The next step is a research prediction that couples acceleration-
aware orientation/motion with wind/forward nuisance parameters and propagates their joint
uncertainty. These fixed-parameter diagnostics establish no refitted power or calibrated result.

## Joint motion/wind prediction and bounded saved-data refits — 2026-10-07

`analysis/tests/joint_acceleration_motion.py` provides a research problem with the existing
wind/wind_tas and sensor-bias parameterization. At every nuisance state it recomputes
high-rate heading, specific-force-corrected gravity/frame, frame derivative/angular rate
and averaged science prediction. Trial wind and forward parameters therefore affect both
motion subtraction and science orientation. Physical TAS still enters the inherited
conditional speed observation. Six added coherent GPS-acceleration/force error modes have
unit Gaussian priors and±3bounds; forward angle is bounded at±3reportedσ. The broad wind
coefficients have±15deg bounds, while physical wind/TAS keeps its existing bounds.

Support is fixed from observable force/GPS and a sufficient norm bound for simultaneous
three-sigma acceleration-mode perturbations. All six cases use83minutes. Sparse trapezoidal
integration maps high-rate frame/rate into those same intervals. Linear science/bias
derivatives are exact; nonlinear state derivatives include both motion and science paths.
Independent directional and physical-column checks pass for both candidates. Sixteen focused
tests pass across the accumulated acceleration, support and joint-prediction fixtures.

Corpus `joint-acceleration-motion-20261007/`: six saved-reference evaluations first report
local joint/conditional covariance, Jacobians and nuisance projection. These are explicitly
data-dependent reference diagnostics, not a design-acceptance envelope. Original preliminary
gyro weights are frozen. Local scienceSD is about0.81/1.23/1.31–1.33 at those reference
states; conditioning the six coherent error modes changes it only slightly. This does not
validate a complete measurement-error covariance or imply those omitted errors are small.

The later "go" covers a bounded existing-recording refit scope: free+three fixed models
per case, at most one predefined free nesting repair per case,≤30optimizer starts including
interruptions, max_nfev200, no bootstrap/new recordings. All24calls completed and converged,
all six objective comparisons nested, no repairs and no all-fit bound flags. All retain the
same83minutes. Free residualRMS: wind8.4921/8.5078/8.5653dph and wind_tas7.9233/8.0283/8.0013dph
for rotating globe/still globe/disc truths, respectively. Completed optimizer time sums
309.864s; wall time was not measured separately. No derived threshold, rejection or winner
is produced. Raw objective differences remain uncalibrated diagnostics.

`refits/plan.json` freezes policy, helper/scientific/input hashes and exact numerical environment,
using one numerical thread. Append-only fsynced optimizer starts/completions, atomic fit
checkpoints and process locking preserve finite scope. Hash/boundary/nesting checks are in
`refit-assessment.json`; resuming after completion skips all fits and retains24starts/24ends.
The six-case authorization is complete; unused call reserve is not a new optimization scope.
No production source, original campaign or eligibility policy changed.

Remaining limitations include original rather than corrected residual weights, incomplete
correlated/instrument error modes, bin-conditioned GPS/TAS likelihood, filter-bandwidth
mismatch and model-dependent acceleration systematics. The next check is matched gyro,
GPS and force filtering and covariance on saved observations before more refits or fresh
calibration. Full production promotion remains premature.

### Saved-data matched output filtering and covariance, 2026-10-07

`analysis/tests/matched_measurement_motion.py` and its readonly review reconstruct the
joint motion at saved free-fit parameters, calibrate and epoch-map raw gyro samples to
disjoint one-second means, and apply identical additional30sHann output filters to gyro
and complete prediction. The joint GPS/force inputs already use30sHann filtering. A
sparse trapezoidal minute operator follows; gaps/turns sever support. This tests bandwidth
sensitivity, not exact equivalence of filtering a nonlinear frame and filtering angular
velocity. Slow science/bias components are lifted linearly within uninterrupted mounting
intervals. No optimizer, synthesis or truth-dependent state selection is involved.

All six checks complete on the same79of83minutes. The regridded unfiltered→matched RMS
is8.2591→7.4033,8.2679→7.4382,8.3178→7.4794dph for wind and7.8545→7.0779,
7.9624→7.2075,7.9290→7.1609dph for wind_tas, in rotating/still/disc truth order.
Legacy residuals on those same minutes are7.8223–8.2810dph. Independent joint-motion
reconstruction closes exactly at saved precision; slow-lift approximation changes minute
prediction0.0255–0.0399dph; gyro regridding changes0.3366–0.3409dph. Additional filtering
reduces variation about9–10%, rather than resolving the remaining gap.

Within-second empirical gyro mean3×3covariances are propagated through `L=A H`,
then back to each bin's sensor frame. `L S Lᵀ` retains shared-sample and cross-axis
blocks; each archived237×237matrix is symmetric positive definite. MarginalRMSsigma
3.5290–3.5307dph assumes independent disjoint seconds and includes within-second motion.
It is not characterized device white noise or a complete likelihood. Reference-frame
fitted residuals have adjacent-minute correlations up to−0.6055, over66contiguous pairs;
nuisance fitting itself can induce correlations. No significance or source attribution
follows. Shared GPS/force errors, calibration/mount errors and fit-induced covariance
remain outside this propagation.

Corpus `matched-measurement-motion-20261007/` contains immutable review, six arrays and
independent verification. Source/input/checkpoint/environment hashes bind the comparison;
verification checks residual arithmetic/common support/prediction closure/PSD and induced
adjacent-minute correlations. Five new tests plus16earlier focused checks pass. Production
source, decisions and eligibility remain unchanged. Next construct a continuous filtered
measurement equation and propagate joint GPS/force/gyro errors, including nuisance fitting,
before any further separately scoped refits or empirical calibration.

### Continuous sampled equation and shared-input propagation, 2026-10-07

`analysis/tests/continuous_measurement_motion.py` replaces the slow-term lift with science
terms and sensor-frame gravity-group offsets/dynamic bias splines evaluated at every GPS
timestamp. Both input/output Hann durations remain30s; filtered longitude derivatives
supply disc transport. Fixed support79minutes. This discrete equation does not establish
exact commutation of nonlinear attitude reconstruction and measurement filtering.

Point-local numerical derivatives are chained through sparse filter/gradient operators,
including `δomega=vee(-D(δC) Cᵀ - D(C) δCᵀ)`. Eleven input channels cover GPS velocity,
height/latitude/longitude and force/gyro axes. Independent-second covariance preserves
speed/bearing-derived north/east covariance, provisional position marginals and empirical
6×6force/gyro covariance. IMU matches are nearest, unique, same-second/epoch, within
0.1sampleperiod; marginals scale1/n_stream, cross blocks matched_count/(n_force*n_gyro).
The strict equal-timestamp preflight failed before evaluation; its plan/status are preserved.

Fixed-parameter propagated sigma11.2533–11.2722dph exceeds residualRMS7.0763–7.4782dph.
Variance contributions: GPS114.15–114.57dph², gyro12.4535–12.4659dph², force~0.0320dph²,
force/gyro cross~0.0010–0.0012dph². GPS dominates this conditional prediction, not a validated
estimate of physical uncertainty. Accuracy fields are provisional sigma scales; equal
independent horizontal marginals, missing GPS correlations and independent seconds are
assumptions. Empirical IMU covariance includes motion. Mount/forward/calibration and
instrument/acceleration/filter systematic uncertainty remain omitted.

The physical wind auxiliary uses the same filtered GPS vector. Its measurement Jacobian
is propagated jointly with gyro residuals. Local penalized Gauss–Newton response at saved
states includes shared-input covariance and deterministic penalties with original weights;
residualsigma11.1343–11.1603dph, science samplingSD~0.168/0.252/0.097. These are not posterior
intervals or identifiability/power evidence; no new optimum was fitted.

Corpus `continuous-measurement-motion-20261007/` freezes six saved tasks, source/input/
checkpoint/environment hashes. Six evaluations complete in93.203summed evaluation-seconds,
one numerical thread,0optimizer/flights/bootstrap. Checkpoints/lock support interruptions;
completed resume skips all cases. Independent full-equation direction checks≤1.523e-9
relative error; direct least-squares response≤1.687e-14. Covariance component closure/PSD
and29focused tests pass. Production source/eligibility/decisions unchanged. Next test
time-correlated GPS/IMU error sensitivity before choosing weights or scoping matched refits.

### Temporal shared-input covariance sensitivity, 2026-10-07

`analysis/tests/temporal_measurement_covariance.py` standardizes each input block, takes
the principal symmetric dimensionless correlation root, and scales back to marginal units.
IMU factors are formed in physical sensor axes and mapped through recovered mount matrices;
shared GPS and force/gyro/auxiliary paths stay intact. Exponential elapsed-time covariance
is propagated by forward/backward recurrences, with no dense full timestamp matrix, lag
truncation, missing-data interpolation or added filter/derivative support. Latent covariance
may persist through gaps/turns. Different GPS/IMU blocks remain independent as assumed earlier.

Six saved states, fixed79minutes and marginal scales, durations0/1/5/15/60/300s independently
for GPS/IMU give36scenarios each,216total. Fixed-state sigma11.2533–42.3085dph; local
old-weight deterministic-penalty response residualsigma11.1343–40.6480dph. The largest
residual scale uses GPS15s/IMU300s in all cases. Science samplingSD across the full grid
spans0.1582–1.7052(rotation),0.2373–2.6670(globe transport),0.0962–1.3006(disc transport).
These conditional saved-state sensitivities are not posterior intervals, new optima,
identifiability gates, calibrated significance or characterized device correlations.
The grid does not bound every credible error process or resolve unknown marginal scales,
GPS channel correlations and mount/calibration/systematic uncertainty.

Corpus `temporal-measurement-covariance-20261007/` freezes source/input/checkpoint/parent/
environment hashes. Baseline covariance recovery≤5.240e-15relative; independent dense
240-timestamp kernel checks≤3.444e-12. Component PSD and all216response summaries pass.
Five new tests,34focused total. Six evaluations67.803summedseconds, one numerical thread;
no optimizer/flights/bootstrap. Resume skips completed cases; no active worker. Production
source/eligibility/decisions unchanged. Next verify a covariance-aware research objective
including shared GPS auxiliary covariance before separately scoping refits/calibration.

### Frozen full-covariance objective and explicit wind discrepancy, 2026-10-07

`analysis/tests/covariance_measurement_objective.py` supplies joint residual/Jacobian,
unit-standardized Cholesky whitening, deterministic penalties and separate quadratic,
log determinant, Gaussian deviance/NLL. Residual signs `[+gyro measured-minus-predicted,
+auxiliary]` match propagated covariance; Jacobian `[-J;T]`. Matrices stay frozen across
coefficient changes. Relative correlation eigenvalue cutoff1e-12 rejects singular/unstable
matrices without clipping/jitter. All216supplied matrices pass (minimum margin0.0019545).
Local sampling response and penalized curvature remain separate; no optimizer is invoked.

Six saved states,36matrices each, fixed79minutes: full-matrix quadratic agreement≤4.424e-15,
whitened full-equation direction agreement≤5.806e-10. Independent direct least-squares
sampling covariance checks≤8.786e-15. Evaluation54.164summedseconds. Physical-wind
measurement-only quadratics27,717.55–598,005.30 reveal that GPS input propagation alone
omits the existing conditional speed-constraint discrepancy allowance.

`wind_constraint_discrepancy.py` therefore versions that existing2m/s allowance as independent
auxiliary model covariance, normalized variance1, added to full measurement covariance.
Shared gyro/GPS/auxiliary cross blocks are unchanged. The second216evaluation comparison
gives physical-wind quadratics166.921–335.859 at the same old states; broad-wind controls
unchanged. These are uncalibrated values with different row dimensions across candidates;
no evidence ranking, model winner or covariance selection follows. Direct response
agreement≤2.666e-14; evaluation7.093summedseconds. Forty-four focused tests pass.

Corpus `covariance-measurement-objective-20261007/` and its `wind-discrepancy/` child freeze
source/input/parent/checkpoint/environment hashes, preserve all cases and verify objectives,
response arithmetic/PSD and controls. Resumes skip completed cases; no active worker.
Covariances remain free-state-linearized, not unconditional design quantities; missing
correlations, reference/calibration/systematic uncertainty and physical discrepancy
coverage remain open. Production source/eligibility/decisions unchanged.

Separately authorized and launched on October7:6saved cases, correlation pairs(0,0),(15,15),(300,300),(15,300)s,
free+three fixed-model fits for each,96primaryfits and at most24nesting repairs,120starts
including interruptions; max_nfev200. Retain explicit model discrepancy and freeze each
covariance for model comparisons. No bootstrap/newflight/calibrated decisions. This
comparison has its own frozen plan in `covariance-refits-20261007/`. Worker
`analysis/tests/refit_covariance_measurement.py` preserves completed failures and
nonconvergence, counts interrupted starts and never repeats an interrupted single repair.
Exact linear science/bias Jacobian columns agree with the complete equation's finite
derivatives for both wind candidates. Correlated GLS agrees with an independent closed-form
ridge solution, including fixed science coefficients; truncated journal recovery preserves
the original bytes and rejects malformed complete records. Five new focused tests pass,
15with existing objective/discrepancy controls; two independent projection tests bring
the focused total to17. Execution is complete:96primarystarts/completions,0repair/
interruption/failure, all96converged and all24comparisons nested. No fit is within1%
of a finite bound. Fixed support79minutes throughout; no active worker/newflights/bootstrap.
Optimizer1732.595s, primary launch-to-completion about30.5minutes, one numerical thread.
Six analysis cases share three recordings (one per injected truth) under two nuisance
candidates; correlation assumptions do not supply independent observations.

Free residualRMS ranges6.8535–8.1180dph for broad wind and4.4711–9.8778dph for physical
wind/TAS. Conditional sampling science SD ranges0.1625–1.5032(rotation),0.2480–2.3205
(globe transport),0.4434–1.0958(disc transport), pooling sensitivity assumptions/candidates.
These are conditional linearized sampling diagnostics, distinct from penalized curvature
and unvalidated as intervals. Covariance stays frozen at the previous joint free states.

The injected model has the lowest fixed penalized objective in every comparison. Raw
differences decline sharply with persistence: rotating-truth rotation/still differences
are about430at independent seconds versus4.3–4.6at long/asymmetric persistence; rotation/
disc about67–68versus1.5–2.0. These are repeated checks of the same recordings, not an
accuracy/power/false-rejection experiment. The ordering of the two incorrect globe
alternatives on disc truth can flip, emphasizing partial rather than invented full evidence.

Independent data-only pair projection uses the full whitened residual Jacobian at
each selected free fit, normalized nuisance columns and least-squares cutoff1e-10;
no penalty rows or estimability/decision threshold. Across24comparisons:

| Pair | Retained fraction | Local information |
|---|---:|---:|
| Rotating/still globe | 0.23540–0.52392 | 2.84234–270.83645 |
| Rotating globe/disc | 0.04014–0.14304 | 0.40356–33.97334 |
| Still globe/disc | 0.31746–0.64274 | 1.19915–117.14354 |

This is a fitted-state diagnostic, not the anchor/envelope design acceptance gate.
Rotation/disc remains the weakest geometry direction. Independent checks reproduce
all residuals exactly, direct full-matrix penalized objectives≤6.270e-16relative and
saved full-equation Jacobian directions≤2.358e-10relative. All covariance/support,
fixed coefficients, finite bounds, evaluation limits and journal/checkpoint identities
are verified in `covariance-refits-20261007/verification.json` by
`analysis/tests/assess_covariance_refits.py`. A completed-scope resume skips all24cases
and starts no optimizer. Hardware covariance persistence and systematic/reference/
calibration coverage remain open; no threshold selection, rejection, winner or promoted
eligibility follows. Further campaigns need a separately defined scope.

## Publication sequence

1. Characterize two physical units across axes, signs, slow rates, temperature, orientation and
   power cycles. Estimate scale/misalignment and g-sensitivity matrices with uncertainty; retain raw evidence.
2. Compare constrained time-varying crab, axis/segment noise weighting, segment-aware bootstrap,
   anisotropic calibration magnitude inference and forward-axis uncertainty propagation.
3. Inject known signals into retained real hardware residual series. Simultaneous dual-IMU
   recordings share a flight and cannot be treated as independent flights.
4. Pilot runtime, preregister the required tail precision, then separately approve single-flight
   and pooled campaigns large enough to measure the false-rejection tails with uncertainty.
5. Select production methods and priors from that evidence, publish it and freeze the methodology
   before making primary scientific claims.

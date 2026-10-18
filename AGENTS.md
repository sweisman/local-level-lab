# Repository instructions

Keep this file focused on standing rules and essential continuation pointers. Put methodology
and results in docs/, and runtime state in worker metadata. Do not append session transcripts,
incident histories, personal commentary or historical process IDs.

## Working practices

- For routine process status use `~/venv/bin/python analysis/status.py`;
  `--json` gives structured output and `--study data/<study>` selects an explicit
  freeze. Keep analysis/study-status.json pointed at current/recent monitored jobs.
  The command is metadata-only and never launches or resumes work. Do not generate
  one-off status scripts. See analysis/STATUS.md for counter and lock semantics.
- Keep responses concise. Use the cheapest sufficient verification and bounded output.
  Prefer durable local jobs to repeated probing. Do not reread successful edits.
  Local tests, including computationally intensive suites, need no approval.
  Ask before manually triggering GitHub Actions or delegation.
  Continue the approved analysis roadmap, including new observed-data qualification
  trials and qualified recovery runs, without requesting renewed permission.
  Freeze each new study and record finite start/evaluation limits before launch;
  keep the four-thread total limit and never expand an active or completed allowance.
- Prioritize diagnostics that help resolve the remaining stretch, particularly
  timing-boundary stopping and repeat disagreement. Defer broader covariance,
  publication and unrelated diagnostic expansion while this recovery work proceeds.
- Leave unfamiliar paths outside the documented corpus alone. Do not scan, document,
  ignore or stage them, and do not inspect unrelated credentials.
- Perform git operations only when explicitly requested. Bundle related work into one
  logical commit; completion does not authorize committing or pushing.
- Run shell steps separately. Avoid command chains and output-trimming pipelines.
- Use ~/venv/bin/python and its pip. For Java, use ~/.local/jdk21 with JAVA_HOME set.
- Future work may use at most four total numerical threads across all active jobs.
  Count workers × numerical threads per worker; one worker × four threads, two × two,
  or four × one are valid. Reserve capacity for other running jobs before launching.
  New numerical commands must use analysis/tests/run_numerical.py (or the same
  lll.compute_budget guard in a new launcher) before numerical imports; specify the
  target's actual worker count and --reserved-threads for other active allocations.
  Freeze that allocation. Preserve frozen studies' original thread settings on resume;
  completed freezes retain their recorded allocations; new jobs may use up to four.
- Write public documentation in plain language. Define IMU before using it. Explain
  purpose, methodology, status and limitations; avoid JSON links in the main README.
  Public docs describe the project, not private collaboration: omit personal requests,
  chat handoffs, permission conversations and reminders addressed to a future author.
  Express planned work as project goals; keep agent instructions here.
  Lead with observed model comparisons; replace blanket "conditional" labels with specific
  remaining checks. Unfinished fits are not equal model support. Raw increments do not by
  themselves establish absence of onboard filtering or corrections.
  Separate geometry, measured angular motion/background field and causal interpretation.
  “Rotating/still globe” are model names for specified-field/zero-field predictions;
  a fit preference does not identify the field's cause or establish a cosmology.
  Do not claim equal support for untested mechanisms or a measured sidereal/solar
  distinction from a fit that fixes the background rate.

## Scientific boundaries

- Additional-source inventory: docs/external-imu-data/README.md and
  data/external-imu-survey-20261018/. Each source may have separate predeclared
  eligibility criteria; keep the existing 53-stretch cohort unchanged. ESA has a
  verified nine-file iMAR catalog and one inspected 8.49-hour original, with GNSS
  PPP export. See its separate receipts; do not rerun the completed full-file scan.
  FTPS uses the explicitly trusted leaf certificate in esa-sample/ftps-peer.pem
  and ~/.esa-ftps.netrc through curl; never print or copy credentials into reports.
  SmartPNT fused reference tracks are context only; raw RINEX
  observations are separate. The long-file range probe verifies endpoints only,
  not interior continuity or stationary conditions. No new fits are authorized
  by metadata acquisition or format inspection alone.

- Select intervals from completeness, receiver data and documented motion/protocol criteria
  before examining Earth-model residuals. Never select favorable gyro values.
- Preserve original measurements, integer increments, timestamps, failures and provenance.
  Reject invalid framing/checksums/truncation; do not silently repair or interpolate science data.
- Keep IMU6, IMU8 and IMU21 conversion hypotheses separate. Distinguish measured properties,
  manufacturer system specifications, hardware-family inferences and assumed bounds.
- Use Applanix Group1 fused navigation for decoder validation and motion context only,
  never independent Earth-model evidence. Archival fits use raw increments and receiver
  measurements. Keep unknown processing/calibration explicit.
- Compare the globe family with the specified stationary disc first. Reveal rotation only
  after converged shape comparisons consistently favor the globe. Relative fit preferences
  do not establish statistical significance; keep the production evidence gate intact.
- Fit complete preselected stretches jointly when their error assumptions are appropriate.
  Fixed 4–10-minute sections check residuals at the same parameters; they are not independent
  trials or fresh calibration fits. Gaps/configuration changes split intervals.
  Joining files requires verified sample, timing and installation continuity.
- Distinguish constant calibration offset, noise and time-varying drift. The ±0.1/±1 degree/hour
  sensitivity cases are assumptions, not verified per-unit limits. Residual checks cannot
  prove stationarity. Specify changing-error models equally for all candidates.
- Keep archival permanent mounts and the passenger IMU-reversal protocol distinct. Do not
  fabricate controls or transfer calibration, performance bounds or thresholds between datasets.
  See [methodology](docs/METHODOLOGY.md) and [archive guide](docs/ILVIS0.md).

## Stationary participant branch

NASA archive analysis remains primary. New crowdsourced sessions follow
docs/STATIONARY.md and docs/PROTOCOL.md: solid level support, same-face A/B reversals,
signed rate estimated without latitude or an expected Earth rate.
Do not restore aircraft identity/flight UX, transfer aircraft thresholds, use absolute
magnitudes as signed rates, or claim consumer sensitivity from NASA results.
Preserve old archives and frozen aircraft studies. New population pooling and calibrated
uncertainty need separate validation; the implemented stationary report always abstains.

## Frozen studies and recovery

- Preserve all 232 retained originals and frozen evidence. Routine continuation does not
  authorize new synthetic campaigns, deletion, budget expansion or production promotion.
- Check status/completion records, start journals and exclusive locks before launch/resume.
  Find current PIDs in metadata. A sandboxed PID lookup alone cannot establish worker death;
  use shared locks or an outside read-only process check.
- Never resume completed studies, duplicate workers, edit active frozen dependencies or mix
  source/input/environment versions. Changed sources require a separately identified freeze.
- Resume only unfinished unchanged work after checking hashes, environment and saved results.
  Interrupted starts remain charged; never reset allowances or rerun failures to improve outcomes.
- Detached workers must persist outside short-lived command sandboxes. Preserve journals,
  atomic hashed outputs and locks. Packaging must not trigger refits.

| Study | Output and guide | Limits / continuation |
|---|---|---|
| Broad corpus | data/ilvis0-corpus-modeling-v2-20261008/; docs/ilvis0-corpus-modeling-20261008/ | Completed and frozen; do not resume. |
| Six-recording refinement | data/ilvis0-shape-refinement-20261008/; docs/ilvis0-refinement-20261008/ | Completed and frozen; packaging only, no resume. Original allowance: 72 primary / 84 maximum starts. |
| All qualifying stretches | data/ilvis0-highspeed-segments-v2-20261008/; docs/ilvis0-highspeed-segments-20261008/ | Completed and frozen; packaging only, no resume. 53 stretches / 318 charged starts; original maximum 424. |
| Matched solver trial | data/ilvis0-solver-trial-20261010/; docs/ilvis0-solver-trial-20261010/ | Completed and frozen; 12 starts, 10 converged fits versus baseline 11. Publication only; no resume or expansion. |
| Saved-parameter residual diagnostic | data/ilvis0-residual-diagnostic-20261010/; docs/ilvis0-residual-diagnostic-20261010/ | Completed and frozen; 24 predictions, zero optimizer starts. Package/render only; no relaunch. |
| Solver qualification controls | data/ilvis0-solver-qualification-20261010/; docs/ilvis0-solver-qualification-20261010/ | Completed and frozen; 34/34 software starts passed, zero observed starts. Package/render only. |
| Matched clock trial | data/ilvis0-clock-trial-20261010/; docs/ilvis0-clock-trial-20261010/ | Completed and frozen; all six fits converged. Globe/rotation preference preserved under header timing. Publication only; no resume or expansion. |
| Z calibration ablation | data/ilvis0-calibration-trial-20261011/; docs/ilvis0-calibration-trial-20261011/ | Completed and frozen; 12 starts, 11 converged, 1,837 evaluations. Gain-zero comparison favors globe; offset-zero comparison incomplete. Publication only, no retries or expansion. |
| Retrospective prediction trial | data/ilvis0-prediction-trial-20261011/; docs/ilvis0-prediction-trial-20261011/ | Completed and frozen; six starts, 887 evaluations, five converged fits. Profiled-removal flat fit exhausted its cap; no retries or expansion. Publication only. |

The six-recording refinement retains four cases. The all-stretch extension uses only ±1°/hour
constant gyro offsets under fixed-zero/profiled Earth-rate removal; ±0.1°/hour is deferred.
Fit all three candidates together, then interpret shape before rotation. Preserve the superseded
zero-start extension freeze at data/ilvis0-highspeed-segments-20261008/; do not resume it.

The all-stretch selector requires at least 240 continuous seconds and every supported receiver
ground-speed sample at least 700 km/h, plus the frozen level-motion/completeness rules.
Save versioned selection before fitting. Publish exact file/hash/UTC interval/duration/speed
in eligible-stretches.csv, all file outcomes in files.csv, and criteria in ELIGIBILITY.md.
Reuse saved intervals; changed policies need a new inventory version. Byte-identical aliases
and overlapping instrument streams must not inflate independent-flight counts.

All numerical studies above are complete; do not relaunch them. The ablation's
one unfinished fit remains unresolved and has no retry allowance. Use
analysis/tests/ilvis0_calibration_trial.py --package-only with its frozen environment
for completed evidence; publication performs no fits.
Use analysis/tests/ilvis0_clock_trial.py --package-only with PYTHONPATH=analysis for
completed clock evidence; packaging performs no fits. Completion records take precedence
over a worker's last in-progress status snapshot.

For completed refinement evidence use docs/ilvis0-refinement-20261008/package_results.py
without --detach. For completed stretch
evidence use analysis/tests/ilvis0_segment_worker.py --package-only with PYTHONPATH=analysis.
Do not rerun numerical studies merely to regenerate documentation.

The metadata-only final summary watcher is docs/ilvis0-highspeed-segments-20261008/summarize_results.py.
Its summary is complete; regenerate with no flags only when needed. It performs no fits.
Post-run diagnosis may read saved fits and selected receiver geometry without new observed starts.
Revised fits need a separately identified development freeze and documented finite compute limits;
never spend the unused allowance of a completed study or tune assumptions to favor a model.

The completed [integration comparison](docs/ilvis0-integration-trial-20261011/README.md)
uses analysis/tests/ilvis0_integration_trial.py and data/ilvis0-integration-trial-20261011/.
Its six starts used 974 native sweeps; four fits converged. No retries, resume or
archive rollout. Package mode performs no fits. Preserve its header clock, bounds,
initialization and ordinary-increment hypothesis; onboard compensation is not established.
The [integration audit](docs/ilvis0-integration-audit-20261011/README.md) reads saved
metadata only. Its first joint grid is complete at data/ilvis0-z-profile-20261011/
and docs/ilvis0-z-profile-20261011/: 27 starts, 4,174 native sweeps, all converged.
Do not resume it or edit its frozen dependencies. The saved-only audit is
docs/ilvis0-z-profile-audit-20261011/; its builder performs no fits or predictions.

Two completed follow-ups use analysis/tests/ilvis0_z_profile_followup.py, separately
frozen under data/ilvis0-z-profile-removal-20261011/ and
data/ilvis0-z-profile-replication-20261011/, with matching docs guides/plans.
Removal completed 27/27 fits; replication completed 25/27. Each spent its 27-start
allowance; no retries, resume or expansion. Original ceiling: 200 sweeps/start, 5,400 total.
analysis/tests/ilvis0_z_profile_sequence.py runs removal then replication, reserving
both worker locks and data/ilvis0-z-profile-followups-20261011/coordinator.lock.
The sequence is complete and its locks are free. Never launch it again. Preserve
stage authorizations, hashes, journals and failures. Publication alone performs no fits.
Keep both completed freezes unchanged, including their shared sources and inputs.
Replication uses only the earliest predeclared September 24 interval and fixed-zero
removal. It is calibration robustness, not the deferred prediction experiment.
No other recording, clock grid, retry or archive rollout is authorized. Publication
is automatic; --study removal/replication --package-only performs no fits.
Superseded zero-start follow-up preparations with the -preparation-v1 suffix are
preserved for provenance; never launch or resume them.
The completed saved-only comparison is docs/ilvis0-z-followup-audit-20261012/.
Its builder checks all 81 fits and 243 residual series without extraction, prediction
or optimization. Preserve both unfinished labels despite passing saved stationarity.
Saved residual covariance is audited in docs/ilvis0-residual-covariance-20261012/.
Its ERROR_MODEL_PLAN.md specifies shared covariance development; no new observed
allowance is authorized. The builder uses saved epochs only; never trigger refits.
Shared covariance controls are complete at docs/ilvis0-error-model-controls-20261012/:
35 analytic checks, no archive reads or observed fits. lll.ilvis0_error_model assumes
known covariance/mean; its predictions omit fitted-parameter uncertainty. Do not
deploy it or interpret its software checks as calibrated observational coverage.
Training/prediction controls are complete at docs/ilvis0-error-training-controls-20261012/.
lll.ilvis0_error_training selects a fixed covariance list on training data only;
prediction includes unconstrained linear-mean uncertainty, not nonlinear bounds or
integrated covariance-parameter uncertainty. No observed allowance or promotion follows.
Nonlinear/boundary diagnostics are checked in docs/ilvis0-nonlinear-uncertainty-controls-20261012/.
Keep active columns in rank checks. Local unconstrained covariance and sampled prediction
ranges are not calibrated intervals. NEXT_PLAN.md guides adapter/freeze preparation;
it authorizes no native observed predictions or fits.
The native adapter is checked at docs/ilvis0-native-uncertainty-controls-20261012/:
six software paths, all 27 columns. Its charged sweeps and training-only geometry
do not qualify archive uncertainty or authorize observed work. The finite proposal is
docs/ilvis0-prediction-covariance-preparation-20261012/README.md: 12 starts, 3,060
sweeps maximum, no retries. Its tested worker is analysis/tests/ilvis0_prediction_covariance_worker.py;
guide/freeze: docs/ilvis0-prediction-covariance-20261012/ and data/ilvis0-prediction-covariance-20261012/.
Its approved finite allowance is recorded in that runtime directory's authorization.json.
Check its lock, metadata and unchanged freeze before resuming unfinished work; never
retry a charged identity or expand its 12-start/3,060-sweep limits. Preparation never
reads originals; launch verifies their saved hashes. Completed work cannot resume.

The matched solver trial is complete; do not launch it again. Publication uses
`analysis/tests/ilvis0_solver_trial.py --package-only`, without observed fits.
The [saved-fit calibration/adequacy audit](docs/ilvis0-calibration-audit-20261010/README.md)
reads published metadata only. Its builder performs no native integration or optimization;
do not mistake saved RMS and fixed-parameter sections for epoch-level or held-out validation.
The [clock/calibration audit](docs/ilvis0-clock-calibration-audit-20261011/README.md) also
uses saved metadata only. Its calibration plan is implemented by the separately frozen,
approved Z ablation above. Zero anchors are diagnostic cases, not measured calibration.
The chronological prediction trial is complete; do not resume or retry its one unresolved
fit. Use analysis/tests/ilvis0_prediction_trial.py --package-only for publication, then
docs/ilvis0-prediction-trial-20261011/build_report.py; these publication steps perform no fits.
Its split is retrospective development evidence, not independent confirmation. Complete
publication only; this allowance authorizes no further numerical studies.
The [epoch residual diagnostic](docs/ilvis0-residual-diagnostic-20261010/README.md) preserves
individual errors under both clocks. Packaging with `ilvis0_residual_diagnostic.py --package-only`
and rendering with its guide's `build_report.py` perform no predictions. Original convergence
labels remain unchanged; clock checks at fixed parameters are not reoptimized fits.

Prioritize recovery of the 41 unresolved stretches. Follow the roadmap's four steps: representative subset,
bounded solver/larger-budget qualification, objective/stopping/prediction repeatability,
then all 41. Keep physical models and bounds fixed and preserve old results. Defer
additional diagnostic expansion. Prepare costed finite freezes and continue this sequence
automatically. No renewed approval is needed within this roadmap; preserve all earlier
results and never spend a completed study's unused allowance.
Recovery subset and all-41 inventory: docs/ilvis0-convergence-recovery-preparation-20261012/.
The completed continuation trial is docs/ilvis0-convergence-recovery-trial-20261012/,
with runtime freeze at data/ilvis0-convergence-recovery-trial-20261012/ and launcher
analysis/tests/ilvis0_recovery_worker.py. Its authorization permits 24 starts /
14,448 sweeps, no retries, and two total numerical threads. It failed qualification;
never resume or reuse its unused allowance. Preserve its source freeze and results.
The saved-only diagnosis and software screen are docs/ilvis0-recovery-diagnosis-20261012/.
The separate rectangular proposal is docs/ilvis0-rectangular-recovery-trial-20261012/,
with completed freeze at data/ilvis0-rectangular-recovery-trial-v2-20261012/ and launcher
analysis/tests/ilvis0_rectangular_worker.py. Its recorded approval permits
24 starts / 14,448 sweeps, no retries, and two total numerical threads. It completed
24 starts / 2,021 sweeps with 8/24 passing fits; qualification failed. Publication is
verified and complete; never resume or reuse unused allowance. Preserve its original
source snapshots, including the subsequently repaired CI test. Preserve the zero-start earlier preparation;
do not launch it. The candidate requires fresh stability, saves local Jacobians and
uses the original physical assumptions. No all-41 rollout follows from software controls.
Saved-tangent diagnosis: docs/ilvis0-rectangular-diagnosis-20261012/; its builder
uses sealed residual/Jacobian artifacts and affine systems only, with no native
predictions or archival fits. Local successes never relabel observed failures.
Exact device characterization is lower-priority parallel work, not a prerequisite for modeling.
Boundary-aware nonlinear software controls are complete at
docs/ilvis0-boundary-controls-20261012/. The separate ilvis0_solver_boundary candidate
passed 40/40 known-answer checks with unchanged bounds and fresh stopping gates.
This is software qualification only; the subsequent observed trial failed qualification.
The report builder defaults to saved-only rendering. Do not rerun completed controls.
The completed analysis/tests/ilvis0_boundary_worker.py study has guide/freeze
docs/ilvis0-boundary-recovery-trial-20261012/ and data/ilvis0-boundary-recovery-trial-20261012/.
It spent 24 starts / 2,399 sweeps, passing 17/24; no test stretch became fully resolved.
Never resume it or reuse its unused allowance. Package completed work only.
Saved-only diagnosis: docs/ilvis0-boundary-diagnosis-20261013/. Six stationary stability
stalls and one budget failure remain; paired tracks agree but stopping outcomes differ.
The separate actual-position candidate is analysis/lll/ilvis0_solver_position.py;
it preserves gradient/cost limits and checks fresh position changes against 1 mm
axis RMS / 1 cm epoch maximum. These are numerical limits, not sensor accuracy.
Current guide/freeze: docs/ilvis0-position-stability-trial-20261013/ and
data/ilvis0-position-stability-trial-20261013/. Launcher:
analysis/tests/ilvis0_position_stability_worker.py. Completed and qualified: 24/24
passing fits, 393 sweeps, all controls and repeats passed. Never restart this trial
or reuse its unused allowance. --package-only performs no fits. Preserve its freeze
and original first-pass labels; the three qualified recoveries are separate results.
Metadata-only full recovery preparation: docs/ilvis0-position-recovery-preparation-20261013/.
Completed full recovery guide/freeze: docs/ilvis0-position-recovery-20261013/ and
data/ilvis0-position-recovery-20261013/. Launcher:
analysis/tests/ilvis0_position_recovery_worker.py --package-only performs no fits.
Completed: 159 starts / 22,355 sweeps, 117 passing fits, all six controls passed.
Combined disposition at that stage: 30 globe / zero flat / 23 unresolved. Preserve the original
freeze, failed primaries and repeats; never restart or reuse unused allowance.
Prioritize overlapping shared flight legs with
mismatched numerical completion, beginning with the three marked recorder pairs in
docs/ilvis0-position-stability-trial-20261013/shared-leg-pairs.csv. Compare common
UTC intervals; preserve each instrument separately and distinguish candidate
same-track grouping from verified aircraft/installation identity. Descriptive gyro
summaries and fused-attitude correction diagnostics do not relabel scientific results.
Saved paired diagnosis: docs/ilvis0-shared-leg-diagnosis-20261014/. It audits sealed
fits and common-time recorder summaries only; no new fits or predictions.
Bounded endpoint diagnostic: docs/ilvis0-shared-leg-probes-20261014/ and
data/ilvis0-shared-leg-probes-20261014/. Launcher:
analysis/tests/ilvis0_shared_leg_probes.py via run_numerical.py. Six diagnostic
identities, ten native calls each, sixty maximum, zero optimizer starts, no retries,
four numerical threads. Completed: six identities / sixty native evaluations.
Never restart or retry. Render its build_report.py without integration;
never relabel failed fits from damped diagnostic probes. Continue with derivative
and integration-precision qualification in the weak gravity/calibration directions;
keep frozen sources, original acceptance rules and earlier evidence preserved.
The completed fixed-endpoint precision study is docs/ilvis0-shared-leg-precision-20261014/
and data/ilvis0-shared-leg-precision-20261014/, launched by
analysis/tests/ilvis0_precision_worker.py via run_numerical.py. Six diagnostic
identities / fourteen calls each / 84 maximum, zero optimizer starts, no retries,
four numerical threads. All 84 evaluations completed; five of six wider probes
passed, including both cost-only failures. The vertical-stability failure remains.
All eleven arithmetic/derivative and six exact-motion solver controls passed.
The completion watcher finished; never restart either worker or watcher. Report-only
build_report.py performs no integration. Preserve frozen source/input snapshots.
Completed paired qualification: docs/ilvis0-paired-precision-trial-20261014/ and
data/ilvis0-paired-precision-trial-20261014/. Launcher:
analysis/tests/ilvis0_paired_precision_worker.py --detach via run_numerical.py.
Sixteen starts / 992 sweeps maximum: 12 primaries and two controls at forty fitting
calls each, two repeats at two hundred each, plus two diagnostic calls/start.
Completed and qualified: 16/16 passing fits, 129 sweeps, both controls/repeats passed.
Never restart or reuse allowance. Combined findings at that stage: 32 globe / zero flat /
21 unresolved. Public tables include qualified primary fits separately from repeats.
Completed bounded recovery: docs/ilvis0-cost-precision-recovery-20261014/ and
data/ilvis0-cost-precision-recovery-20261014/. Launcher:
analysis/tests/ilvis0_precision_recovery_worker.py --detach via run_numerical.py.
Twelve cost-only failure stretches; nine other failure classes excluded. Limits:
86 starts / 5,532 sweeps, four total numerical threads, no retries. Primaries and
two controls have forty fitting calls each; twelve repeats have two hundred each;
each start has two diagnostic calls. Completed: 83/86 fits passed, 891 sweeps; both
controls and all twelve repeats passed. Never resume or reuse its allowance.
Publish only per-stretch complete primary/control/repeat comparisons.
Completed sequential continuation guides/freezes: docs/ilvis0-budget-continuation-20261014/
and data/ilvis0-budget-continuation-20261014/; docs/ilvis0-remaining-precision-20261014/
and data/ilvis0-remaining-precision-20261014/. Both stages and their coordinator
are complete. Never relaunch analysis/tests/ilvis0_precision_continuation_worker.py
or reuse either allowance. Package-only performs no fits. Preserve sources,
reused artifacts and failed charged starts; revised methods require new freezes.
Completed damped-solver qualification: docs/ilvis0-trust-qualification-20261014/ and
data/ilvis0-trust-qualification-20261014/. Do not relaunch its worker or waiter.
Qualification failed on all four starts of nonlinear27; preserve the frozen
candidate and failures. Diagnose that known-answer control before any new candidate
qualification. The planned eight-start archival trial cannot follow this failed gate.
Current publication: docs/ilvis0-current-findings-20261015/; its metadata-only
build_report.py preserves the older findings and copies measured summaries without
decoding originals. Regenerate docs/build_current_status.py afterward; --check
verifies the combined snapshot and landing-page excerpts.
Revised candidate qualification is complete at docs/ilvis0-trust-v2-qualification-20261015/
and data/ilvis0-trust-v2-qualification-20261015/. Never relaunch its completed worker.
The completed matched trial uses analysis/tests/ilvis0_trust_trial_worker.py
with docs/ilvis0-trust-trial-20261015/ and data/ilvis0-trust-trial-20261015/.
Its scope is eight starts / 1,296 native sweeps, four total threads and no retries.
Never relaunch its worker, retry failures or reuse its allowance. Preserve its
candidate and engine snapshots. --package-only performs no fits. Next numerical
work needs separate freezes: the six other unresolved stretches under the hybrid
solver, and a focused saved-endpoint diagnosis of the last trial target. No wider
rollout or relaxed stopping limits follow from partial trial success.
Completed six-target freeze: docs/ilvis0-hybrid-remaining-20261015/ and
data/ilvis0-hybrid-remaining-20261015/; launcher
analysis/tests/ilvis0_hybrid_remaining_worker.py --detach. Limits: 24 starts /
4,528 native sweeps, four total threads, no retries. Eleven failed primaries each
require their own repeat; all pair checks must pass per stretch. Reuse only the
25 hashed passing companions. Completed:
24 starts / 1,336 sweeps, 7/24 passing fits, both controls passed, one stretch recovered.
Combined findings: 47 globe / zero flat / six unresolved. Never resume or reuse allowance. Preserve its
planner, candidate and engine snapshots. No wider allowance follows.
The separate saved-only audit is docs/ilvis0-final-stability-audit-20261015/ and
data/ilvis0-final-stability-audit-20261015/. It is complete: render only with
build_report.py --render-only; do not replay its four affine solves as a new result.
INTERPRETATION.md describes the timing-direction discrepancy. Native perturbation
checks need their own finite freeze; the audit authorizes no new fits or label changes.
The first timing diagnostic is complete at docs/ilvis0-timing-derivative-20261016/
and data/ilvis0-timing-derivative-20261016/: the control used ten calls; both target
identities failed preflight with zero calls. Preserve all errors; never restart it.
The separate corrected diagnostic uses analysis/tests/ilvis0_timing_worker_v2.py,
docs/ilvis0-timing-derivative-v2-20261016/ and data/ilvis0-timing-derivative-v2-20261016/.
Completed: two endpoints / 24 native calls, zero optimizer starts, four threads.
Never restart it. Preserve the one-epsilon coupled-bound adjustments and all results.
The separate packet-aware solver is analysis/lll/ilvis0_solver_timing.py.
Its sealed software qualification passed 67/67 at
docs/ilvis0-timing-solver-qualification-20261016/ and
data/ilvis0-timing-solver-qualification-20261016/. Never rerun the completed batch.
The completed matched observed trial uses analysis/tests/ilvis0_timing_trial_worker.py,
docs/ilvis0-timing-trial-20261016/ and data/ilvis0-timing-trial-20261016/.
Completed: four starts / 237 native calls, 2/4 passing fits; both controls passed,
target primary and repeat failed fresh stability. Qualification failed. Never
restart, retry or reuse its unused allowance. Preserve the five reused companions,
sources and evidence. Packaging performs no fits. Continue saved-result diagnostics
of the stopping gate and other unresolved endpoints; no wider solver rollout follows.
The saved-only stopping audit is complete at docs/ilvis0-stopping-audit-20261016/
and data/ilvis0-stopping-audit-20261016/: 22 endpoints over all six unresolved
stretches, 66 saved affine solves and five independent gate controls, no native
predictions or observed fits. Never rerun its charged numerical batch; build_report.py
--render-only packages saved results. interpret_results.py reads sealed metadata only.
All eleven unfinished primaries cluster within 1 µs of packet boundaries, with timing
as their largest gradient component. Keep failures and dispositions unchanged.
The separate exact-knot stopping policy is analysis/lll/ilvis0_boundary_stop.py.
Its qualification passed 43/43 at docs/ilvis0-boundary-stop-qualification-20261016/
and data/ilvis0-boundary-stop-qualification-20261016/. Never rerun the sealed batch.
It is software qualification only; no archive adapter or labels are qualified by it.
Saved-clock preparation is complete at docs/ilvis0-boundary-adapter-preparation-20261016/
and data/ilvis0-boundary-adapter-preparation-20261016/: 22 endpoints / 7,197 clock
queries, zero native predictions or observed fits. Never rerun its batch;
build_report.py --render-only packages saved metadata. All nineteen unfinished
endpoints support side geometry; keep three passing smooth repeats unchanged.
NEXT_PLAN.md proposes adapter controls then a finite native diagnostic for all six:
nineteen time-only searches plus two controls, 546 calls maximum. Preparation
authorizes no launch until its runner, qualification and new freeze are complete.
Adapter software qualification passed 30/30 at docs/ilvis0-boundary-adapter-qualification-20261016/;
native callback qualification passed 2/2 at docs/ilvis0-boundary-native-qualification-20261016/.
Both sealed batches are complete; never rerun them. The all-six diagnostic is
docs/ilvis0-boundary-diagnostic-20261016/ and data/ilvis0-boundary-diagnostic-20261016/,
launched by analysis/tests/ilvis0_boundary_diagnostic_worker.py. It stopped after
eight saved checks and one interrupted identity; its truncated journal blocks resume.
Never restart it or repair the journal. The saved-only accounting audit is
docs/ilvis0-accounting-audit-20261016/; receipt qualification passed 18/18 at
docs/ilvis0-receipt-qualification-20261016/. Never rerun either sealed batch.
The unstarted-only continuation at docs/ilvis0-boundary-continuation-20261016/
and data/ilvis0-boundary-continuation-20261016/ completed twelve identities /233 calls
within its 312-call ceiling and four-thread allocation. Never restart or reuse its allowance.
Its zero-evaluation reporting error and the old interrupted identity remain failures.
The saved-only review at docs/ilvis0-boundary-review-20261016/ verifies all companions,
controls and repeats, adding one globe preference: totals at that stage 48/0/5. Never rerun
its arithmetic batch. Use render_report.py for publication only; the original frozen
builder has a receipt self-inclusion defect on repeated rendering. Continue saved-only
diagnosis of remaining timing solutions before freezing more native work.
The adjacent-boundary follow-up uses analysis/tests/ilvis0_boundary_followup_worker.py,
docs/ilvis0-boundary-followup-20261016/ and data/ilvis0-boundary-followup-v3-20261016/.
Its frozen controls passed 65/65 at docs/ilvis0-boundary-followup-controls-v3-20261016/.
Limits: two smooth controls (three calls each), the bb8061a43b4f14b6262ceda1
unsubtracted zero-field-globe primary/repeat (thirty calls each), 66 total calls,
four total threads, no retries. Completed: four identities /44 native calls, all
four passed. Never restart, retry or reuse its unused allowance. Package-only
performs no fits. Its saved-only review at docs/ilvis0-neighbor-review-20261017/
passed the required repeat and companion checks: totals at that stage 49/0/4. Never
rerun that review’s single numerical batch; --render-only publishes saved evidence.
Preserve the earlier zero-start preparations and qualification snapshots. Live
status publications are excluded from numerical inputs; frozen task geometry and
original hashes remain required. Continue finite timing-basin/calibration work on
the remaining four stretches; a reporting-only repair cannot resolve repeat disagreement.
Saved timing-basin comparison is complete at docs/ilvis0-timing-basins-20261017/
and data/ilvis0-timing-basins-v2-20261017/: eight pairs /sixteen local projection
solves, zero native predictions. Never rerun the numerical batch; --render-only
publishes saved evidence. Preserve the earlier pre-comparison schema failure.
The fixed-time profile is frozen at data/ilvis0-fixed-time-profile-20261017/ with
guide docs/ilvis0-fixed-time-profile-20261017/ and launcher
analysis/tests/ilvis0_fixed_time_worker.py. Its separate qualification passed 21/21,
including three compiled-motion controls, at docs/ilvis0-fixed-time-controls-20261017/.
Scope: two smooth controls (three calls each), four 50f24131843071ae9312c082
conditional nuisance fits (80 fitting calls plus one diagnostic call each), 330
native calls maximum, four total numerical threads, no retries. Completed: six
identities /23 calls; both controls passed, four final diagnostics failed accounting
after conditional stopping checks. Never restart or reuse allowance; preserve errors.
The separate saved-endpoint verification uses analysis/tests/ilvis0_profile_verification_worker.py,
docs/ilvis0-profile-verification-20261017/ and data/ilvis0-profile-verification-20261017/.
Its eight software checks passed using the real receipt ledger. Limits: four
diagnostic identities /12 native calls, zero optimizer starts, four total threads,
no retries. Completed: 4/4 endpoints verified, twelve native calls; both within-anchor
repeat checks passed. Never restart or reuse its allowance. Preserve both exact
timing anchors, saved endpoints and frozen sources. Package-only performs no native calls. Conditional verification cannot
replace the full free-time gate or change the scientific disposition.
Interior timing-profile guide/freeze: docs/ilvis0-interior-timing-profile-20261017/
and data/ilvis0-interior-timing-profile-20261017/. Launcher:
analysis/tests/ilvis0_timing_profile_worker.py through run_numerical.py. Its eleven
software controls passed. Scope: three interior time offsets crossed with both
verified nuisance starts, six fits /486 native calls, four total numerical threads,
no retries. Completed: six fits /36 native calls, all six and three repeat pairs
passed. Never restart or reuse unused allowance. Preserve frozen sources/inputs.
Package-only performs no native calls. A coarse fixed-time profile
cannot qualify a full free-time fit or change findings; revised solver work needs
its own finite qualification after interpreting this profile.
Profile-seeded trial: analysis/lll/ilvis0_profile_seeded.py and launcher
analysis/tests/ilvis0_profile_seeded_worker.py; guide/freeze at
docs/ilvis0-profile-seeded-trial-20261017/ and data/ilvis0-profile-seeded-trial-20261017/.
The finite proposal is two fresh controls and two free-time fits: four charged
identities /two optimizer starts /174 native calls, four total threads, no retries.
All five verified timing points per nuisance start are reused for seed selection;
time and every other original parameter are free in the new fits. All 24 software
checks passed before the observed freeze. Stopped with 53 charged calls: both
controls passed, the primary failed time stationarity, and the charged repeat
was interrupted. Its incomplete receipt transaction blocks resume; never repair,
restart, retry or reuse its remaining allowance. Preserve all saved results,
pending transactions and frozen sources. The saved-only audit at
docs/ilvis0-profile-seeded-audit-20261017/ and data/ilvis0-profile-seeded-audit-20261017/
is complete: three saved results and one clock-geometry check (344 queries), zero
native calls/fits/original reads. Use build_report.py --render-only for publication;
never rerun its metadata batch. The failed primary is about 1.24 ns from a supported
integration knot. Next native work should check both sides of that exact boundary
under a new finite freeze, retaining original stopping/repeat limits and all failures.
Successful full gates and repeats still need a saved companion/model review before
any published disposition changes.
Exact-boundary diagnostic: analysis/tests/ilvis0_profile_boundary_worker.py,
docs/ilvis0-profile-boundary-20261017/ and data/ilvis0-profile-boundary-20261017/.
Its eleven software controls passed. Limits: four diagnostic identities /66
native calls, zero nonlinear optimizer starts, four total numerical threads,
no retries. Sources are the completed failed primary, separately verified profile
companion and two passing controls; never retry the interrupted free-time start.
Preserve the source-to-final movement gate, exact clock checks and all failures.
Check status, locks, hashes and receipts before continuation; never duplicate or
restart completed work, retry charged identities or reuse unused allowance.
Do not edit active frozen dependencies. Package-only performs no native calls.
The exact-boundary study is complete: four identities /24 native calls, both
controls passed and both target left checks failed. Never restart, retry or
reuse its remaining allowance. The saved-only left-side audit at
docs/ilvis0-left-boundary-audit-20261017/ and data/ilvis0-left-boundary-audit-20261017/
is complete (two saved target reports, zero native calls/fits). Render only;
never rerun its metadata batch. It motivates searching the close boundary cluster
without relaxing the final stationarity gate.
Clustered-boundary launcher: analysis/tests/ilvis0_clustered_boundary_worker.py;
guide/freeze docs/ilvis0-clustered-boundary-20261017/ and
data/ilvis0-clustered-boundary-20261017/. All twelve software checks passed.
Scope: four diagnostic identities /58 native calls, zero nonlinear optimizer
starts, four total numerical threads, no retries. It reuses the verified executor
in a private, checked adaptation; never edit the completed template or active
search/source dependencies. Preserve exact scopes, source-to-final movement,
full two-sided gate and endpoint repeat checks. Check status, locks, hashes and
receipts before continuation; never duplicate or restart completed work, retry
charged identities or reuse unused allowance. Package-only performs no native
calls. Completed: four identities /54 native calls, all passed. Never restart
or reuse its allowance. The saved companion/model review is complete at
docs/ilvis0-cluster-review-20261018/ and data/ilvis0-cluster-review-20261018/:
one saved residual-pair comparison, zero native calls/fits/original reads.
All six primaries, both controls and the newly checked diagnostic repeat pass;
current totals are 50/0/3. Use build_report.py --render-only; never recompute its
single numerical batch. The diagnostic repeat comes from the separately verified
profile companion; it does not relabel the interrupted free-time fit. Prioritize
the three remaining IDs in docs/NEXT_STEPS.md under separate finite freezes.
Remaining time-profile launcher: analysis/tests/ilvis0_remaining_time_profile_worker.py;
guide/freeze docs/ilvis0-remaining-time-profile-20261018/ and
data/ilvis0-remaining-time-profile-20261018/. All 25 software checks passed,
including three compiled-motion controls. Scope: 0e73879f98c3b701fd7c42df,
zero-field globe under both processing cases, two exact saved time anchors per
case crossed with both nuisance starts; eight conditional fits and two fresh
controls. Limits: ten identities /654 native calls, four total threads, no retries.
Check locks, metadata, receipts and unchanged freeze before resuming unfinished
work; never duplicate or restart completed work or reuse its allowance. Preserve
the completed executor template and every frozen dependency. Package-only makes
no native calls. Completed: all ten identities passed, 83 native calls; never
restart or reuse its allowance. Fixed-time fits cannot change the 50/0/3 tally.
Next free-time test: analysis/tests/ilvis0_remaining_free_time_v2_worker.py;
guide/freeze docs/ilvis0-remaining-free-time-v2-20261018/ and
data/ilvis0-remaining-free-time-v2-20261018/. All 38 software checks passed.
Scope: same stretch and both zero-field-globe processing cases, two fresh controls
and four free-time fits. Limits: six identities / four optimizer starts / 342 native
calls, four total numerical threads, no retries. Both verified offsets per start
are retained for deterministic seed choice; all original parameters then become
free. Preserve full stationarity, physical stability and per-case repeat gates.
Check locks, metadata, receipts and freeze before continuation; never duplicate or
restart completed work or reuse its allowance. Do not edit frozen dependencies.
Package-only performs no native calls. Successful fits still need a saved review
of all companions before any published disposition changes.
Completed: six identities /198 native calls; both controls passed, all four targets
failed full gates despite within-case repeat agreement. Never resume or reuse its
allowance. Saved-only diagnosis: docs/ilvis0-remaining-free-time-audit-20261018/;
four endpoints, 1,336 clock-geometry queries, zero native calls/fits/original reads.
Use build_report.py --render-only; never repeat its charged geometry batch.
Timing-only stationarity fails without removal; profiled removal fails the fresh
cost/stationarity correction while physical-position limits pass. Next work needs
a separate finite source-preserving boundary/correction diagnostic, not relaxed gates.
That diagnostic is frozen at data/ilvis0-remaining-boundary-20261018/ with guide
docs/ilvis0-remaining-boundary-20261018/ and launcher
analysis/tests/ilvis0_remaining_boundary_worker.py. All 18 software checks passed.
Limits: six diagnostic identities, 110 native calls, zero optimizer starts,
804,096 clock queries, ten affine solves, four total numerical threads, no retries.
It checks both controls and all four saved endpoints under both processing cases
with the existing source-preserving cluster helper. Keep full two-sided gates and
case-separated repeat checks; neither timing-only search nor repeat agreement alone
qualifies a result. Check locks, receipts, metadata and source/environment hashes
before continuation. Never retry charged identities, restart completed work or
reuse unused allowance. Package-only performs no native calls. Do not edit frozen
sources, inputs or PLAN.md while active. A pass still needs saved companion review.
Completed: six identities /82 native calls. Both controls and the profiled-removal
pair passed; both unsubtracted endpoints failed the spacing/geometry guard.
Never resume or reuse this completed allowance. Saved-clock diagnosis is complete
at docs/ilvis0-narrow-boundary-audit-v2-20261018/: two reports, twelve clock-state
queries, zero native calls/fits/original reads. Render only; do not rerun it or
the superseded failed metadata batch. NEXT_PLAN.md specifies representability-aware
software qualification before a separate 58-call observed diagnostic. Preserve
scientific stopping tolerances and all failures. ESA selection remains a proposal
at docs/external-imu-data/ELIGIBILITY_PLAN.md; metadata checks authorize no ESA fits.
Representability candidate: lll.ilvis0_representable_boundary and launcher
analysis/tests/ilvis0_representable_worker.py; guide/freeze at
docs/ilvis0-representable-boundary-20261018/ and data/ilvis0-representable-boundary-20261018/.
All 31 qualification checks passed (40 compiled-motion calls, six compiled clock
comparisons). It changes only probe geometry qualification: distinct exact clock
states and an eight-ULP parameter margin. Scientific stopping limits stay fixed.
Limits: four diagnostic identities /58 native calls /zero optimizer starts,
402,048 clock queries, six affine solves, four total threads, no retries. Check
locks, receipts, metadata, source hashes and environment before continuation;
never retry charged identities, restart completed work or reuse unused allowance.
Completed: four identities /56 native calls, all four passed. Never restart or reuse
its allowance. Preserve frozen dependencies; package-only performs no native calls.
The saved companion/model review is complete at docs/ilvis0-representable-review-20261018/
and data/ilvis0-representable-review-20261018/: two saved repeat-pair comparisons,
zero native calls/fits/original reads. All six primaries, fresh controls and both
required repeat pairs pass; totals at that stage are 51/0/2. Preserve all ten diagnostic
outcomes, including the earlier geometry failures. Use build_report.py --render-only;
never recompute its batch. Current remaining targets are listed in docs/NEXT_STEPS.md.
Saved final-two diagnosis: docs/ilvis0-final-two-audit-20261018/; nine reports and
fourteen branch summaries, zero native calls/solves/fits. Complete; render only.
Focused nearby-pair launcher: analysis/tests/ilvis0_final_pair_worker.py;
guide/freeze docs/ilvis0-final-pair-boundary-20261018/ and
data/ilvis0-final-pair-boundary-20261018/. Software qualification passed 33/33,
including 40 compiled-motion calls and six clock comparisons. Limits: four
diagnostic identities /58 native calls, zero optimizer starts, four total threads,
no retries. Target only 370cec66878c4c1cf84b4ceb profiled-removal specified-field
primary/repeat, from the complete original saved fits; preserve the older
interrupted diagnostic. Check locks, receipts, hashes and environment before
continuation; never duplicate or restart completed work or reuse its allowance.
Keep its sources and PLAN.md unchanged while active. Both fresh controls, full
two-sided/source-movement checks and repeat comparison must pass; a separate
saved companion/model review is still required before changing 51/0/2.
The first focused nearby-pair trial is complete: two controls passed, two targets
failed saved-context preflight with zero target calls; six native calls total.
Never restart it or reuse its allowance. The separate corrected-context worker is
analysis/tests/ilvis0_final_pair_v2_worker.py, with guide/freeze
docs/ilvis0-final-pair-boundary-v2-20261018/ and data/ilvis0-final-pair-boundary-v2-20261018/.
It checks numerical receiver-coordinate rows and exact relative epochs through
lll.ilvis0_saved_context before original extraction. Limits remain four identities /
58 native calls, zero optimizer starts, four threads, no retries; sources and
identities are separately frozen. Preserve both older preflight errors and the
interrupted original diagnostic. Never edit completed source files to repair this
new study. A full pass still requires a saved companion/model review.
The corrected-context trial is complete: 54 native calls, two controls passed,
both targets failed right-side fresh stability despite repeat agreement; no
software errors. Never restart it or reuse its allowance.
Saved correction audit: docs/ilvis0-correction-audit-20261018/ and matching data/;
complete six affine solves /four SVDs, zero native calls. Render only; never
repeat its numerical batch. INTERPRETATION.md identifies an affine solve that
reports success while worsening its own objective relative to a feasible zero step.
Range-scaled candidate/trial: lll.ilvis0_scaled_branch and
analysis/tests/ilvis0_scaled_pair_worker.py; docs/ilvis0-scaled-pair-boundary-20261018/
and matching data/. Software qualification passed 33/33, including 40 compiled
motion calls and six clock comparisons. Limits: four identities /58 native calls,
zero optimizer starts, four total threads, no retries. Only 370cec66878c4c1cf84b4ceb
profiled-removal specified-field primary/repeat and two fresh controls are included.
Preserve the qualified sources, exact bounds, full native stopping gates and
corrected context. Check locks, hashes, receipts and environment before continuation;
never duplicate/restart completed work or reuse unused allowance. A complete saved
companion/model review is required before any change to 51/0/2.
The range-scaled observed trial is complete: all four checks passed, 54 native
calls; never restart or reuse its allowance. The saved complete review at
docs/ilvis0-scaled-pair-review-20261018/ and matching data/ is complete: two saved
pair comparisons, all six primaries and both required pairs pass, twelve focused
outcomes preserved, zero native calls/fits/original reads. Render only; never
recompute its batch. Current totals: 52 globe /zero flat /one unresolved. The last
target is b4e44ddc0f130ecd45674c78; separate its timing-profile disagreement from
local calibration/geometry failures under a new finite freeze. Preserve all
earlier source snapshots, preflight errors and failed native gates.
Last-stretch field-endpoint launcher: analysis/tests/ilvis0_last_field_worker.py;
guide/freeze docs/ilvis0-last-field-boundary-20261018/ and matching data/.
Qualification passed 34/34, including 40 compiled-motion calls and six clock
comparisons. Limits: six identities /110 native calls, zero optimizer starts,
four total threads, no retries. Only b4e44ddc0f130ecd45674c78 specified-field
primary/repeat under both processing cases and two fresh controls are included.
The separate zero-field timing profile is not included or qualified by a pass.
Check locks, receipts, hashes and environment before continuation; preserve
active frozen sources/PLAN.md, never duplicate or restart completed work and
never reuse allowance. Both case-specific pairs must pass; keep 52/0/1 until
all zero-field/flat companions and the complete scheduled repeats are qualified.
The final-stretch field study is complete: all six checks passed, 100 native calls,
both processing-case repeat pairs passed. Never restart or reuse its allowance.
Final zero-field timing profiles: analysis/tests/ilvis0_last_time_profile_worker.py;
docs/ilvis0-last-time-profile-20261018/ and matching data/. Qualification passed
26/26 with three compiled-motion controls. Limits: ten identities, eight conditional
profile starts, 654 native calls (80 fitting +one full diagnostic per profile,
two controls at three calls), four total threads, no retries. Both exact saved
offsets are crossed with both original starts in both processing cases; preserve
the exact +0.15 s bound anchor. Check locks, hashes, environment and receipts before
continuation; keep frozen sources/PLAN.md unchanged, never duplicate/restart
completed work or reuse unused allowance. A fixed-time pass cannot relabel the
stretch; require a separately frozen full free-time check and complete review.
Final zero-field profiles are complete: ten checks passed, 132 native calls,
all four conditional repeat pairs passed. Never resume or reuse the allowance.
The separate full free-time launcher is analysis/tests/ilvis0_last_free_time_worker.py;
guide/freeze docs/ilvis0-last-free-time-20261018/ and matching data/. Scope:
only b4e44ddc0f130ecd45674c78 zero-field globe, both processing cases and both
original nuisance starts, seeded from the verified profiles. Limits: six charged
identities, four optimizer starts, 342 native calls, four total threads, no retries.
Check locks, receipts, environment and hashes before resuming unchanged unfinished
work. Never restart completed work, retry charged identities or expand the allowance.
Keep all original active parameters and physical/stopping bounds; complete saved
companion-model review is required before changing the public disposition.
The final free-time trial is complete: six identities, 190 native calls, both
controls passed but all four targets failed full stability. Never restart or
reuse its allowance. Saved-only diagnosis is complete at
docs/ilvis0-last-correction-audit-20261018/ and matching data/: twelve affine
solves, eight spectra, 1,334 saved-clock queries, zero native calls/original reads.
Use build_report.py --render-only; do not replay the completed batch.
Next boundary launcher: analysis/tests/ilvis0_last_zero_boundary_worker.py;
guide/freeze docs/ilvis0-last-zero-boundary-20261018/ and matching data/.
Scope is only the four completed final-stretch zero-field endpoints under both
processing cases, plus two fresh controls. Limits: six identities /110 native
calls, zero optimizer starts, 804,096 clock queries, ten affine solves, four total
threads, no retries. Use the qualified scaled/representable two-sided checker;
do not change physical or full native stopping limits. Check locks, receipts,
environment and source hashes before unchanged unfinished continuation. Never
duplicate workers, restart completed work, retry identities or reuse allowances.
Complete companion-model review remains necessary before changing 52/0/1.
Final zero-field boundary checks are complete: six passed, 102 native calls,
both processing-case repeat pairs passed. Never resume or reuse the allowance.
The complete saved-evidence review is docs/ilvis0-last-review-20261018/ and
matching data/: four pair comparisons, zero observed starts/native calls/original
reads. All six primaries, four original required repeats and both fresh controls
pass. Use build_report.py --render-only; never replay the completed batch.
Combined disposition is 53 globe /0 flat /0 unresolved. Numerical recovery of
the original 41 unfinished comparisons is complete; do not launch more recovery
work. Preserve earlier failures and conditional-only profile labels. The next
priority is the measurement-contribution study, then predictive adequacy,
residual uncertainty and shared-flight dependence in docs/NEXT_STEPS.md.
Current publication verifies the old interrupted manifest through its exact
public source-freeze copy; do not alter either historical manifest to match it.
Preserve the zero-start first preparation at data/ilvis0-remaining-free-time-20261018/;
its duplicate-source-lock failure spent zero native calls and must not restart.
The v2 launcher deduplicates source locks and checks its complete qualified source
set. Its earlier software-only qualification remains separate from the final
software-controls-revised freeze; neither authorizes repeated observed starts.
The separate [rotation-field measurement](docs/ROTATION_FIELD.md) will infer the retained background vector
before interpreting its cause, with aircraft motion, transport and calibration fitted jointly.
The proposal authorizes no new fits or campaign budget. Do not fix or subtract the standard
Earth rate to create the estimated field, or fit an original field and unconstrained onboard
subtraction as independently identifiable quantities.

The saved prediction audit and analytic solver screen are complete at
docs/ilvis0-prediction-audit-20261011/. Regenerate its audit from metadata only;
screen_solvers.py --render-only preserves the completed software screen. The unit-scale
candidate's v2 study at data/ilvis0-unit-scale-trial-v2-20261011/ and
docs/ilvis0-unit-scale-trial-20261011/ is completed and frozen: six starts, five converged,
749 evaluations. Its report watcher completed; do not relaunch either process.
The saved solver diagnosis at docs/ilvis0-solver-diagnosis-20261011/ performs no fits.
Its STOPPING_PLAN.md and ilvis0_solver_verified_stop.py describe a separately tested
candidate. Do not relabel old failures or expand completed allowances.
The verified-stop trial at data/ilvis0-verified-stop-trial-20261011/ and its guide in
docs/ilvis0-verified-stop-trial-20261011/ is complete and frozen; do not relaunch its
worker or watcher. Qualification failed; no retries, replication or archive rollout
are authorized. Its saved-only diagnosis is docs/ilvis0-verified-stop-diagnosis-20261011/;
next work follows docs/ILVIS0_DIAGNOSTIC_PLAN.md. Preserve the
superseded zero-start v1 preparation without running it. The two-recording replication
selection and NEXT_PLAN.md authorize no observed starts or archive-wide rollout.

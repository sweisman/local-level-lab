# Repository instructions

Keep this file focused on standing rules and essential continuation pointers. Put methodology
and results in docs/, and runtime state in worker metadata. Do not append session transcripts,
incident histories, personal commentary or historical process IDs.

## Working practices

- Keep responses concise. Use the cheapest sufficient verification and bounded output.
  Prefer durable local jobs to repeated probing. Do not reread successful edits.
  Ask before expensive new work or delegation; stay within approved compute scopes.
- Leave unfamiliar paths outside the documented corpus alone. Do not scan, document,
  ignore or stage them, and do not inspect unrelated credentials.
- Perform git operations only when explicitly requested. Bundle related work into one
  logical commit; completion does not authorize committing or pushing.
- Run shell steps separately. Avoid command chains and output-trimming pipelines.
- Use ~/venv/bin/python and its pip. For Java, use ~/.local/jdk21 with JAVA_HOME set.
- Use at most two total numerical threads/workers; do not multiply worker and BLAS
  concurrency. Preserve frozen studies' original thread settings on resume.
- Write public documentation in plain language. Define IMU before using it. Explain
  purpose, methodology, status and limitations; avoid JSON links in the main README.
  Lead with observed model comparisons; replace blanket "conditional" labels with specific
  remaining checks. Unfinished fits are not equal model support. Raw increments do not by
  themselves establish absence of onboard filtering or corrections.
  Separate geometry, measured angular motion/background field and causal interpretation.
  “Rotating/still globe” are model names for specified-field/zero-field predictions;
  a fit preference does not identify the field's cause or establish a cosmology.
  Do not claim equal support for untested mechanisms or a measured sidereal/solar
  distinction from a fit that fixes the background rate.

## Scientific boundaries

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
Revised fits need a separately identified development freeze and explicit finite compute allowance;
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
do not qualify archive uncertainty or authorize observed work. Prepare a finite
comparison and durable launcher before requesting a new numerical allowance.

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

After current numerical work is complete and reviewed, the proposed next scientific stage
follows the [analysis roadmap](docs/ANALYSIS_ROADMAP.md): qualify the solver, audit calibration
boundaries and absolute adequacy, then test timing/coordinate sensitivity and recording dependence.
Exact device characterization is lower-priority parallel work, not a prerequisite for modeling.
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

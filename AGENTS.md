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
  after converged shape comparisons consistently favor the globe. Conditional numerical
  preferences are not calibrated decisions; keep the production evidence gate intact.
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

After checking locks and the unchanged unfinished freeze, run the appropriate launcher with
PYTHONPATH=analysis and OPENBLAS_NUM_THREADS=2, OMP_NUM_THREADS=2, MKL_NUM_THREADS=2:

- ~/venv/bin/python analysis/tests/ilvis0_shape_worker.py --detach
- ~/venv/bin/python analysis/tests/ilvis0_segment_worker.py --detach

Restore the refinement report watcher, if absent, with
~/venv/bin/python docs/ilvis0-refinement-20261008/package_results.py --detach.
For completed refinement evidence use that script without --detach. For completed stretch
evidence use analysis/tests/ilvis0_segment_worker.py --package-only with PYTHONPATH=analysis.
Do not rerun numerical studies merely to regenerate documentation.

The metadata-only final summary watcher is docs/ilvis0-highspeed-segments-20261008/summarize_results.py.
Its summary is complete; regenerate with no flags only when needed. It performs no fits.
Post-run diagnosis may read saved fits and selected receiver geometry without new observed starts.
Revised fits need a separately identified development freeze and explicit finite compute allowance;
never spend the unused allowance of a completed study or tune assumptions to favor a model.

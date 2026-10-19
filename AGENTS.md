# Repository instructions

Keep this file limited to standing rules. Put methodology, plans and findings in
`docs/`, and execution state in worker metadata. Do not append study inventories,
progress counts, session histories, personal commentary or process IDs.

## Working practices

- Keep responses concise and verification proportionate. Prefer durable local jobs
  to repeated probing. Do not reread successful edits.
- Continue the approved roadmap through its qualification gates without repeatedly
  requesting permission. Local tests, including intensive suites, need no approval.
  Ask before manually triggering GitHub Actions or delegating work.
- Perform git operations only when explicitly requested. Bundle related work into
  one logical commit; completion does not authorize committing or pushing.
- Leave unfamiliar paths outside the documented project corpus alone. Do not scan,
  document, ignore or stage them, or inspect unrelated credentials.
- Run shell steps separately, without command chains or output-trimming pipelines.
- Use `~/venv/bin/python` and its pip. For Java, use `~/.local/jdk21` and set
  `JAVA_HOME` accordingly.

## Compute and execution safety

- Use at most **four total numerical threads** across all active jobs. Count
  workers × threads per worker and reserve capacity for other running jobs.
- Launch numerical commands through `analysis/tests/run_numerical.py`, or the
  same `lll.compute_budget` guard, before numerical imports. Declare the actual
  worker count and reserved threads. Preserve a frozen study's original allocation.
- Before each new study, freeze its question, inputs, source/environment hashes,
  selection policy, thread allocation and finite start/evaluation limits.
  Never expand an active allowance or spend unused allowance from completed work.
- Check completion records, journals and exclusive locks before launching or
  resuming. A sandboxed PID lookup alone cannot establish that a worker is dead.
  Completion records take precedence over stale progress snapshots.
- Never restart completed studies, duplicate workers, edit active frozen
  dependencies or mix source/input/environment versions. Resume only unfinished,
  unchanged work after verifying its hashes and saved results.
- Charge starts and evaluations before execution. Interrupted starts remain charged;
  never reset allowances or retry failures to improve outcomes. Preserve failures.
- Detached workers must survive short-lived command sandboxes. Preserve durable
  journals, atomic hashed outputs and exclusive locks. Packaging must never refit.
- A failed qualification blocks dependent observed fits. Saved-data diagnosis and
  separately frozen software qualification may continue within the approved roadmap.
  Routine continuation does not authorize unrelated campaigns, deletion or promotion
  of research results into production decisions.
- Use `~/venv/bin/python analysis/status.py` for status, with `--json` or
  `--study data/<study>` as needed. Maintain its registry rather than creating
  one-off status scripts. Keep live state in worker metadata.

## Scientific integrity

- Select intervals using completeness, receiver trajectory and documented motion
  criteria before examining model residuals. Reuse versioned saved selections;
  changed criteria require a separate policy and inventory.
- Preserve retained originals, integer increments, timestamps, provenance and
  frozen evidence. Reject invalid framing, checksums and truncation. Do not silently
  repair or interpolate scientific measurements.
- Keep IMU conversion hypotheses and dataset-specific assumptions separate.
  Distinguish measured properties, system specifications, hardware-family inferences
  and assumed calibration bounds. Exact hardware documentation is supporting work,
  not a prerequisite for modeling with explicitly stated assumptions.
- Use Applanix Group 1 fused navigation only for decoder validation and motion
  context, never independent Earth-model evidence. Fits use recorded inertial
  increments and receiver observations. Raw increments alone do not establish
  absence of onboard calibration, filtering or compensation.
- Compare the globe family with the specified stationary disc first; interpret
  background-field comparisons only after complete shape comparisons favor globe.
  Preserve required model/case, control and repeat checks. Do not relax acceptance
  limits or relabel failed fits from diagnostic probes.
- Fit complete preselected stretches jointly when the error model supports it.
  Fixed sections at the same parameters are diagnostics, not independent trials.
  Split at gaps or configuration changes. Joining files requires verified sample,
  timing and installation continuity; overlapping recorders are not independent flights.
- Distinguish constant offsets, noise and changing drift. Assumed offset bounds
  are not measured device limits; residual checks do not prove stationarity.
  Apply changing-error models equally to all candidates.
- Removing an observation requires explicit replacement constraints and
  initialization. Do not reintroduce omitted gyro/acceleration information through
  fused attitude or hidden assumptions. Keep all nuisance columns in rank checks.
  Numerical completion, physical adequacy and calibrated uncertainty are separate.
- Infer a freely measured rotation field without fixing or subtracting the target
  rate to create it. An original field and unconstrained onboard removal cannot
  be identified separately from their retained combination.

## Public documentation and participant experiment

- Write plain language for nonspecialists. Define IMU before using it; explain
  purpose, method, findings and specific limitations. Keep the homepage brief and
  avoid JSON links there. Public pages describe the project, not private collaboration.
- Separate geometry, measured angular motion and causal interpretation.
  “Rotating/still globe” name specified-field/zero-field models, not cosmologies.
  Do not claim significance, equivalent support for untested mechanisms, or a
  sidereal/solar distinction from a comparison that fixes the background rate.
- Archive analysis is primary; stationary consumer crowdsourcing is secondary.
  Follow the stationary protocol: solid level support, same-face reversals, and
  signed-rate estimation without latitude or an expected Earth rate. Do not restore
  aircraft identity/flight UX or transfer archival thresholds to consumer devices.
  Keep permanent aircraft mounts, historical passenger studies and stationary
  controls distinct. Pooling and detection claims require separate validation.

## Project references

- [Methodology](docs/METHODOLOGY.md) and [archive guide](docs/ILVIS0.md).
- [Next analyses](docs/NEXT_STEPS.md), [technical roadmap](docs/ANALYSIS_ROADMAP.md)
  and [study index](docs/STUDIES.md); individual plans and receipts define frozen scope.
- [Verified findings](docs/CURRENT_STATUS.md) and [status-command guide](analysis/STATUS.md).
- [Additional data sources](docs/external-imu-data/README.md),
  [stationary experiment](docs/STATIONARY.md) and [participant protocol](docs/PROTOCOL.md).

# Core pipeline and prospective comparisons

The follow-up software is implemented and checked with controlled fixtures. No new campaign,
actual-route replay, optimizer search, calibration or validation has run. The previous 72-case
comparison remains the latest campaign evidence. The recording app is unchanged.

An **IMU (inertial measurement unit)** measures turning and acceleration. The new research
tools simulate its behavior along a fixed airline route and ask which turn times preserve
useful Earth-model comparisons despite wind and instrument errors.

## Implemented work

- A shared aircraft-motion mask checks integrated IMU turns. Aircraft maneuvers or unverifiable
  GPS make later orientation unresolved. Geometry search adds a configurable two-minute buffer.
- Optional design calculations check all model anchors across crab/wind states, forward-angle
  uncertainty and mount-epoch perturbations. The weakest retention/information sets the score.
  Geometry search uses beam 16 and known assumed axes, with no simulator or nonlinear fit.
- Wind, mixed bias, correlated noise and temperature are composable with independent named RNG
  streams. Wind changes assumed aircraft heading/airspeed while preserving the recorded ground path.
- Optional direct pair profiles use their own convergence, nonlinear bootstrap and prior gates,
  and the pair difference before the global science cutoff. Integrity and selection checks remain.
  Their thresholds/pooling method differ from older comparisons; mixed methods are rejected.
- Diagnostics retain the original session, available turn inputs/mount matrices/bins/fit rows
  and analysis or failure. Unreached stages have no fabricated arrays.

The default three-model rule and numerical cutoff are preserved. The envelope is a finite
development grid, not a guarantee for every nuisance state or reconstructed orientation.
No final empirical decision threshold or real-IMU evidence has been added.

## Seven archived tracks

Five windows have two frozen replay specifications each. Two remain coverage-blocked.

| Window | Permitted five-minute-grid turns with the two-minute buffer |
|---|---|
| ORD–AUH | 10, 15, 30, 40 minutes |
| AUH–ORD | None |
| ORD–LAX | None |
| SEA–KEF | 45 minutes |
| FRA–JNB | 20, 30, 40, 60 minutes |
| SIN–DPS; DXB–JNB | Blocked by coverage; no replay scheduled |

These are preparation-only checks on an assumed interpolated path, including its course and
climb variation. They do not establish actual aircraft motion between fixes or an optimized schedule.

The **observed-fix** mode retains original observations and unknown accuracies. The **simulated
frequent-GPS** mode assumes a smooth path between nearby fixes and generates simulated GPS and
IMU readings. Estimated positions and intervals over 90 seconds split support. Neither bridges
long gaps. Source timezone/altitude reference remain unknown; the clock is synthetic and reported
altitude is assumed geometric height. Empirical policies are refused pending domain enforcement.
This does not enable an operational external-GPS fallback.

## Unrun proposal and cost

The proposed matrix has 1,440 replay and 720 timing-control evaluations: **2,160 total**, using
paired fresh seeds 600600–600602, three truths, four nuisance scenarios, two crab fits and
anchor/envelope-profile candidates. These are repeated fits of shared simulated recordings,
not independent flights. Bootstrap is zero; this cannot establish error tails.

Timing controls include the original 75/90-minute schedules, the second 90-minute turn shifted
by ±5/±10 minutes, and the earlier correction. The ±10-minute single-turn shifts violate unchanged
spacing and are blocked. The remaining controls each fail at least one buffered maneuver check;
unsafe controls must abstain and cannot become recommendations. Per-route search should precede
choosing an informative replay schedule.

Historical analysis cost was 7.18 seconds per evaluation. New envelope/profile runtime and
diagnostic storage are unmeasured. Search bounds total 2,580,930 SVD evaluations per objective
across the five routes, with four objectives proposed; no searches have run. A separately
authorized bounded timing/storage pilot and search budget are needed. **Authorized attempts: zero.**

## Files and commands

`proposal.json` freezes implementation/configuration/policy/two-thread environment and source
hashes. `optimizer-estimates.json` retains maneuver checks and cost bounds. `trajectories/`
contains the ten hashed replay specifications. Historical evidence is unchanged. Preparation
tool `analysis/tests/prepare_core_pipeline.py` runs no flight/search/SVD scoring and refuses overwrite.

After compute approval, `research.py` accepts `--geometry observed --trajectory SPEC`,
`--design-mode envelope --pairwise-method profile`, and `--diagnostics-root DIRECTORY`.
Requested profile bootstrap requires `--bootstrap-refit nonlinear`. `optimize_turns.py` supports
`--track-plan`, `--track-id`, `--comparison`, `--maneuver-buffer-s` and `--estimate-only`;
the old complete-pipeline search requires `--mode pipeline`. Use the existing virtual environment
and at most two total CPU threads. A manifest is not run permission.

**177 focused checks passed in 5.97 seconds**, covering encoded replay, fixed ground path/gaps,
unsafe turns, diagnostics, optimizer ordering/caching, profile fitting/eligibility/calibration
compatibility/pooling and prior/bootstrap failure abstention. These fixtures are software checks.
Physical wind/TAS, modeled magnetic ambiguity, operational domain enforcement and sharded execution
remain deferred. Magnetic exclusions remain. Final-domain approval, fresh calibration and independent
validation still require separately authorized work.

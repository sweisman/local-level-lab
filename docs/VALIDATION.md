# Software 0.6.0 validation and publication boundary

The correctness release preserves the physical model, provenance architecture, raw schemas 2/3
and WMM sensitivity check. Dynamic crab, noise weighting, bootstrap dependence, forward-axis
uncertainty and pooled significance remain research questions. Real slow-rate bench evidence and
demonstrated false-rejection tails remain publication blockers after these software corrections.

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

This is additional analysis work. The running development campaign uses its original simulated
GNSS assumptions and makes no external-track recovery claim. Collection may preserve a useful
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
death and Bluetooth recovery on both physical IMUs remain part of BENCH.md.

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

Scott authorized 1,000 additional development attempts, about 3–3.5 hours, instead of the full
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

Scott authorized the [eight-case plan](development-1000-20261005/watchdog-diagnostic-plan-20261006.json).
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
No stress flights, information/SVD evaluations or observed-trajectory replay have run. The latter
still requires trajectory integration and checked simulated mount/sensor/nuisance assumptions.

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

No additional compute is authorized. Prospective geometry review precedes final envelope approval;
source changes require another freeze. Fresh calibration must generate actual primary/pairwise
threshold files before independent validation can be frozen. Real IMU bench work awaits hardware.

## Experimental partial pairwise evidence

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

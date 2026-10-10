# Next steps for the NASA airborne analysis

## Starting point

The completed study found **12 globe preferences, zero complete flat preferences and
41 unfinished comparisons** among 53 eligible stretches. All 12 complete globe results
also favor rotation. These are useful findings; unfinished calculations do not provide
equal support for flat Earth. The [findings](ilvis0-highspeed-segments-20261008/FINDINGS.md)
and [saved-result diagnosis](ilvis0-highspeed-segments-20261008/POST_RUN_REVIEW.md)
preserve what the measurements and calculations currently show.

An **IMU (inertial measurement unit)** measures turning and acceleration. These are
survey-grade IMUs used for precision airborne mapping. Their published capabilities
provide a meaningful foundation for error assumptions. Exact device characterization
and producer documentation are **lower-priority parallel work**, not prerequisites for
continuing analysis. Use available system/family specifications, empirical decoder checks
and explicitly stated assumptions; investigate how those assumptions affect results.
Do not transfer one configuration's exact specifications to every recording or call an
assumed offset allowance measured drift. Unknown corrections matter where they prevent
a particular quantity from being separated, rather than stopping all modeling.

The next milestone is a comparison with finished fits for all three models, an adequately
fitting preferred model, explained calibration behavior, and a preference that survives
justified timing and observation alternatives. Independent replication then tests its
generality. Numerical completion, fit adequacy and statistical support are separate checks.

## Priority and scope

The [matched trial](ilvis0-solver-trial-20261010/RESULTS.md) is now complete: 10/12 fits
converged versus 11/12 in its baseline. The control kept its globe/rotation preference;
the other stretch remains unresolved. The
[saved-fit calibration/adequacy audit](ilvis0-calibration-audit-20261010/README.md) now
reports signed limits, parameter associations, local weak directions and residual RMS
for all 318 first-pass and 12 trial fits. The
[two-recording residual diagnostic](ilvis0-residual-diagnostic-20261010/README.md) has
completed 24 saved-parameter predictions with no refits. It reproduces baseline errors,
finds temporal correlation after whitening, and exposes a large vertical clock effect.
Independent solver qualification and matched reoptimized timing/calibration tests remain planned.

| Order | Work | What can happen without new observed fits? | Deliverable |
|---|---|---|---|
| 1 | Qualify the solver after the completed matched trial | Review preserved successes and failures; no rollout based on this trial. | Independent numerical controls and matched baseline comparison. |
| 2 | Diagnose calibration-boundary saturation | Recover signed parameter values, limit frequencies and associations from saved fits. | Calibration-model adequacy audit, beginning with Z-axis gyro gain and offset. |
| 3 | Assess absolute fit quality | Inventory saved residual diagnostics and missing channels. New predictions or refits require a separate scope. | Per-fit adequacy report and a tested path toward an absolute-fit criterion. |
| 4 | Test clock and receiver-coordinate sensitivity | Specify matched alternatives and choose intervals from saved geometry/numerical diagnostics. | Small frozen comparison matrix, with all three models treated equally. |
| 5 | Analyze completion selection and recording dependence | Use saved fits, receiver tracks and recorded provenance. | Completion analysis and a conservative flight/installation grouping ledger. |
| Parallel, lower priority | Seek exact device and processing records | Continue the existing inquiry; record what each source actually establishes. | Better-supported assumptions where information becomes available. |
| Follow-on | Measure the background rotation field | Prepare the estimator design and separation checks after current numerical work is reviewed. | Freely estimated field before interpretation of its cause. |

This roadmap authorizes no new observed starts, synthetic campaigns, deletion, resumption
of completed studies or production promotion. The current solver trial retains its
12-start/200-evaluation limit. Any new numerical work needs a separately identified
configuration and finite approved allowance. At most two total numerical threads/workers.

## 1. Qualify numerical completion

Review the [matched solver trial](ilvis0-solver-trial-20261010/README.md) against the
preserved baseline: objective values, stationarity, stability, boundary behavior and
predicted observations. A materially worse completed control or unexplained change in
ranking needs investigation before expansion. Do not simply promote the 42 old
budget-stopped fits that happened to pass stationarity.

Add bounded qualification controls generated independently of the fitting kernel:
known interior and boundary optima, transport-only and background-rotation inputs,
nearly redundant parameters, timing perturbations, and several deterministic seeded
starting points. The existing analytic solver tests are a start, not an independent
end-to-end IMU/GPS qualification. Check objective agreement and prediction recovery;
require parameter recovery only for combinations the controls identify. Count every
start and evaluation. Multi-start agreement improves confidence but does not prove a
global optimum. Distinguish a converged but poor flat fit from an unfinished flat fit.

## 2. Explain calibration-boundary saturation

The first pass reached the Z-axis gyro-gain limit in **304/318 fits** and its offset
limit in **294/318**. The median completed fit had 15 parameters at a limit. A constrained
optimum can legitimately sit on a boundary; this frequency warrants its own audit.

For every parameter, report its physical estimate, normalized distance to each limit,
upper/lower boundary counts, model/case dependence and associations with clock, mounting,
speed and latitude. Examine Z-axis gain and offset together. Across-fit correlations of
estimates describe the archive; they are not within-fit parameter uncertainties. Use
projected gradients and available Jacobian singular vectors to examine local trade-offs.
The baseline saved singular values alone; do not pretend it contains those vectors.

Specify a **small calibration sensitivity matrix before new fits**, justified by published
survey-system performance and the physical meaning of each error. Separate constant
offset, gain error and changing drift. Vary the suspect gain/offset limits in controlled
steps; hold other assumptions fixed, then test only a justified interaction. Apply every
case equally to rotating globe, still globe and flat disc. Preserve preferences, failures,
residuals and boundary behavior whether or not they favor globe.

Success means either explaining why a boundary is physically appropriate or showing a
stable preference under defensible alternatives without systematic unexplained extremes.
Do not add unrestricted time-varying bias just to improve residuals or choose limits that
produce a desired shape. Exact per-unit certificates are not required to run these tests.

## 3. Assess absolute model adequacy

Every completed fit should report physical horizontal/vertical residuals, whitened RMS,
residual quantiles/outliers and temporal dependence. Whitened residuals are errors scaled
using the declared GPS covariance. Test their distribution and autocorrelation against
what that covariance predicts; a small relative model cost does not establish that the
covariance or preferred model is adequate.

Plot residuals against receiver speed, latitude, height, elapsed time and independently
available maneuver indicators. Use measured temperature only if a documented channel
exists. Elapsed time or aircraft movement must not be relabeled sensor temperature.
Store epoch-level residuals and weights in a new diagnostic artifact if the old outputs
lack them; generating predictions still has a numerical cost even without optimization.

The completed two-recording diagnostic now stores per-epoch errors under both clocks and
both covariance assumptions. Its nominal rotating-globe residuals are small but retain
lag-one correlations of roughly 0.42–0.76. Packet-header timing raises vertical RMS
to approximately 9.2–9.4 m without changing fitted parameters. These findings prioritize
the clock comparison; they neither establish a calibrated adequacy failure nor replace
held-out prediction checks. Speed/course covariates in this diagnostic are coordinate-derived
proxies under a reference globe metric, not recorded VTG measurements or independent evidence.

Retain the whole-stretch fit as the primary analysis. Existing fixed-parameter 4–10-minute
section checks remain useful, but **are not held-out validation**: the parameters saw
those observations. A genuine blocked prediction check fits calibration/initialization
using training receiver observations only and evaluates withheld receiver positions using
the original IMU increments. Account for correlated GPS errors across the split and fitted
parameter uncertainty. When a short stretch cannot support a meaningful split, report
that limitation and use separate-flight validation; do not invent independent trials.

Develop and validate an absolute-fit criterion before it can authorize positive scientific
support. Account for fitted parameters, active bounds, correlated errors and solver failures;
do not assume a textbook chi-square cutoff applies automatically. Calibration must cover
the full hierarchy, including the minimum of the two globe costs and the selection process.

Public reporting should distinguish:

- **Preferred model:** the complete matched comparison has a lower cost.
- **Adequacy not established:** required absolute-fit checks are missing or unvalidated.
- **Preferred but inadequate:** the relative winner fails established fit-quality checks.
- **Validated support:** numerical, adequacy, robustness and statistical decision checks pass.

These future labels do not retrospectively change the current findings. The existing
production significance gate stays intact until the additional checks are validated.

## 4. Compare timing and receiver-coordinate assumptions

First fit nominal 200 Hz and packet-header elapsed timing on a small, fixed set with
equal calibration freedoms for all three models. Include a representative control and
high clock-sensitivity cases chosen from saved diagnostics, not from desired model
preferences. The old fixed-parameter check showed median residual ratios near 1.01–1.02
but 95th-percentile ratios near 17–22; refitting is necessary to distinguish calibration
readjustment from a persistent timing problem. Report changes in costs, ranking,
completion, boundary saturation and absolute fit quality.

Then compare full three-dimensional receiver positions with horizontal-only observations,
an altitude-only diagnostic and justified height/geoid perturbations. Preserve original
reported heights and geoid separations. Clearly identify which coordinates enter the
objective, initialization and motion screening. Removing altitude from the objective
alone does not mean it disappeared from the complete procedure. Check identifiability
after each ablation; an insufficient observation set cannot supply a positive conclusion.

Transform covariance consistently with any coordinate representation. Equivalent
representations of the same physical observations should agree numerically; do not
compare arbitrary coordinate units as if they carried equal information. For an axis
ablation, use its appropriate covariance rather than dropping components after joint
whitening. Receiver latitude/longitude remain outputs of a geodetic navigation system;
these tests isolate their influence, not replace them with raw GNSS ranges. Raw ranges
are a possible later extension, not a blocker for the present archive study.

Stage these comparisons rather than immediately multiplying every timing, calibration
and coordinate option into a large grid. Freeze each small matrix and its compute budget
before fitting, and add combinations only when earlier diagnostics justify them.

## 5. Account for completion selection and dependence

Report completion by model: rotating globe **43/106**, still globe **73/106**, flat disc
**72/106**. Analyze its relationship to pre-fit observables: duration, latitude, ground
speed, heading evolution, recorded IMU type and installation signature. Keep fitted
Jacobian conditioning in a separate numerical diagnostic; it is not an independent
pre-fit observable. With only 53 stretches, prefer a small descriptive analysis to an
overfitted prediction model. Do not select new intervals by whichever model finishes.

Build a grouping ledger using verified dates, platform information, time overlap, source
aliases and installation continuity. Distinguish a POS system identifier from a physical
IMU serial number. Where actual flight or device identity is uncertain, record that and
use conservative grouping. Several stretches or simultaneous IMU streams from one flight
must not become several independent confirmations. Hold out whole supported flight or
installation groups for replication; never randomly split overlapping samples.

Joint calibration across stretches is a later useful test **only where installation
continuity is supported**. Matching configuration bytes alone do not justify it. Model
appropriate temporal changes equally for every candidate and charge its added complexity.
Manufacturer replies can improve that support without holding up the other audits.

## Rotation-field follow-on and publication

The [rotation-field proposal](ROTATION_FIELD.md) remains separate: fit a retained
background vector freely, examine latitude/altitude/velocity dependence, then interpret
its cause. It will reuse the numerical, adequacy and dependence checks above. It need
not wait for an exact hardware identification, but unknown upstream subtraction must
not be fitted as though it were independent of an unknown original field strength.

Publish methods and empirical conclusions at the level actually supported. A methodological
paper can describe the inverse-navigation framework and verified controls even when many
real fits remain unfinished. Stronger empirical claims require adequate, robust comparisons
and genuinely independent replication. Continue preserving original increments, receiver
observations, selection, failures, source/environment hashes and complete reporting receipts.
Keep consumer-IMU development secondary; it does not resolve these archival questions.

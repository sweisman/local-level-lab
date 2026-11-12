# Attribute the failed long noisy forecasts

## Question

The completed twenty-minute generated study fitted each physical candidate to
its own noisy measurements. All 24 fits passed numerical checks, yet later
horizontal errors were 83.6–88.6 m. A separate known-calibration calculation
puts the expected horizontal error scale under the declared noise law at
33.77 m. Determine the error of **the same realized noisy IMU streams** when
the generating calibration and starting state are supplied as a diagnostic.
This separates one realized noise path from additional error introduced by
calibration estimation; it does not assign all remaining error to a single cause.

## Fixed development scope

Use only the closed [twenty-minute noisy study](../esa-noisy-prediction/README.md)
and its six unique combinations of three generating models and two processing
settings. Starts and receiver-error policies reuse the same sensor stream within
each combination, so they are not new noise realizations. Keep the original
55° generation latitude, noise seed, sampling times, recorded-increment input law, physical equations,
forecast boundary and later truth. No original aircraft file, reserved ESA
flight, independent noise seed, fit or optimizer start enters this diagnostic.
Regeneration charges the same deterministic random variates again under a
separate finite allowance.

Use the parent's frozen geometry and calibration definitions; restore a
frozen dependency when needed rather than substituting changed current code.
Regenerate each stream from versioned source and require the raw noisy
angle, velocity and interval arrays to match the original study's saved hashes
for **both starts and both receiver policies**. A mismatch stops the diagnostic;
do not replace the historical source with current code on trust. Bind every
input, source, compiler and numerical environment in a new study manifest.
The current input and noise modules differ from the parent's frozen bytes
because later point-error support was added. The original increment-error
branch appears unchanged on source review, but only the complete regenerated
array hashes can establish that it reproduces this parent. Restore its frozen
dependency if they differ.

For each matched stream, supply the known generating calibration, true
starting state and generating gravity anchor only to an oracle forecast. The
original fitter's force-derived gravity initializer remains part of the
preserved comparison; it is not silently reused as truth. Save the oracle
forecast and input hashes
before opening the generated later truth. Score the same 400 later receiver
epochs in north/east/up metres. Report the oracle error beside all four
historical fitted errors for that stream, with the original numerical and
accuracy labels unchanged. The oracle is not a permitted real-flight estimator
and cannot be used to select a model.

The value-only adapter will derive the known start from the generating model at
time zero, use the 1,500 m gravity anchor fixed by the climb generator, and
evaluate the complete recorded-increment history with the existing native
`ConditionalProblem` value predictor. It will use two placeholder receiver
epochs solely to satisfy the problem interface; no measured receiver
coordinates enter the oracle forecast. The full 1,200-epoch prediction is saved
before the
noiseless later receiver positions are generated for scoring. A short
known-correction numerical control must pass before source-bound preparation.

## Finite execution and interpretation

Prepare six task identities, at most one forecast native call per task and no
optimizer calls. The native packet/query charge ceiling is six times
360,000 intervals times 1,200 receiver epochs; source construction and random
variates receive separate prepaid limits. Use two one-thread workers and a
two-hour cooperative wall ceiling. Before preparation, qualify and
freeze task-level recovery under the shared study lifecycle: sealed complete
results, including numerical failures, must be reused; only unfinished
technical attempts may receive separately charged finite recovery attempts
under unchanged inputs and method. A finite worker-loss/reboot test and an
idempotent resume command are required. If that gate fails, do not launch.
The frozen recovery policy allows at most three starts per task and twelve
technical interruptions across the study. Its continuation has a separate
24-hour wall ceiling and requires at least 10 GiB free before dispatch.
Preserve
all failures and charges, then independently audit the saved arrays, forecasts
and scores before publication.

Each task also prepays construction of 360,000 intervals, 362,002 generated
samples and 6,484,812 normal variates. The sample allowance covers the
360,801 samples used to rebuild the historical sensor input, one true
starting-state sample, and 1,200 receiver samples generated only after the
forecast is saved. These charges are separate from its one native value call
and must reconcile with the construction journal.

Read-only preflight of the published closed parent verifies its report's 24
numerical passes and 24 physical-accuracy failures, then finds exactly six
sensor-stream hash groups, with four historical fits per group. The shared
`lll.noisy_realization_attribution.bound_streams` check requires the full case
matrix and identical angle/velocity/time array hashes within each group. Three
focused known-answer tests pass, including closed-parent reading and rejection
of a changed stream. The real closed parent yields six bound tasks, six native
calls and 2,592,000,000 maximum packet/query visits. This preflight does not
regenerate or score a forecast.

The preparation gate binds the six parent streams, exact source bytes,
the numerical environment and a finite task manifest. Its fourteen focused
non-numerical tests pass, including byte-level rejection of a changed
regenerated sensor stream, the known-correction bound map and saving a forecast
before later truth is opened.
The orchestration also rejects an incomplete parent before construction and
rechecks the stream before scoring. The repository
source closure resolves. The
numerical known-correction test now passes for all three candidate models and
both processing cases. The shared task-recovery code passes five focused
interruption tests, and its existing source-bound qualification verifies against
the current recovery implementation. Preparation now requires that qualification
and freezes its request and report with the study inputs. The complete oracle
qualification must be refreshed after this source change; no new study has been
prepared or launched. The evaluator checks the closed parent,
rebuilds and hashes each sensor stream, accounts for the true start and later
receiver truth, and seals its forecast before scoring. Its full native path is
not yet qualified through the complete six-task study.
The saved-result comparison requires all four historical fitted failures for
each oracle stream and rejects a rewritten historical success label.
The separate read-only audit opens only a closed study, verifies source and
charge records, replays saved physical scores, and packages a short public
comparison. Its closed-study, report-rendering and saved-score numerical replay
tests pass. Publication remains contingent on qualified recovery and a
finished, independently verified six-task study.
The short known-correction test covers all three candidates and both
processing settings, with one native value call per case.

An oracle error near the original fitted error would implicate the realized
input errors or propagation assumptions. A much smaller oracle error would
identify an additional calibration/initialization contribution. Either way,
this single shared noise seed cannot establish a probability distribution,
aircraft error coverage or Earth-model significance. Any later accuracy rule
requires its own prior freeze and independent validation.
The task's `passed` field records successful technical execution; the separate
`accuracy_all_sections` field reports the existing physical accuracy screen.
Neither is an Earth-model decision.

[Error-model gate](../integrated-noise-covariance/NONLINEAR_PLAN.md) ·
[Known-calibration error scale](../noisy-prediction-benchmark/README.md) ·
[Study index](../STUDIES.md).

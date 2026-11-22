# One sealed generated case: joint-profile nonlinear replay

Source: the completed `straight-level` task in
`data/generated-matched-one-sided-v2-20261117`. It gave one generated
recording to all three physical candidates and sealed every fit and
earlier-only forecast before scoring later receiver observations. Use the
exact same recipe, seed, training rows, source closure and numerical
environment. All 249 recorded source hashes currently match the checkout.
The new study has **one task, one worker, one numerical thread, no new fit
starts, and a one-hour wall ceiling**. Keep it separate from the source
study and preserve any technical failure.

For each candidate, regenerate the same IMU and training receiver input;
load its sealed fitted normalized calibration. Recreate the candidate
training problem and native forecast. Before reading the sealed later
generated observations, require the recreated forecast coordinates to
match the sealed coordinates and its training error/operator binding to
match the sealed artifacts. Save the full future Jacobian, fixed operator
configuration, bounds and their hashes. Retain all 26 calibration columns.

Only after all three input replays pass, read the sealed generated later
receiver path. Use the [conditioned joint whitening](CONDITIONAL_JOINT_PROFILE_RESULT.md)
and [bounded whole-path profile](JOINT_FUTURE_PROFILE_RESULT.md) for each
candidate. Then evaluate the same native path at each profiled calibration
point to measure the **nonlinear Taylor remainder**. Report future profile
cost, rank, boundary hits, correction size, tangent-versus-native path
difference and the original whole-path range outcome separately. Use the
same coordinate chart and fixed receiver error law for all three.

This is development diagnosis, not a calibrated model test: later data
choose the profile correction; the source noise law is synthetic; one case
cannot establish coverage, power or a null distribution. Do not revise
the source study's abstentions or open observed/protected flights. The
technical gate is exact source/input/forecast replay and finite, fully
accounted calculations. A scientific threshold is deliberately absent.

Before launch, freeze exact per-task native-call/packet limits, generated
sample counts, environment/source hashes, a passing source qualification,
and a task-level reboot/worker-interruption recovery check using `lll.studies`.
An unsuccessful replay blocks dependent scoring; it does not authorize
changed tolerances or a rerun of completed tasks.

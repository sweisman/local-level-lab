# Continuation from the sealed development pilot

## Fixed question

Can the missing receiver-measurement bound for the `point` error law be
completed from the original saved ESA recording-187 fit and forecast, without
refitting either law or changing the scientific inputs, error laws, calibration
limits, candidate model or withheld split? The parent pilot remains a terminal
technical failure. This is a **new, separately charged continuation**.

## Input and proof obligations

Bind the parent completion, source/environment manifest, original training
IMU/receiver inputs, and the hash-verified partial artifacts: both fits, both
forecasts, the first law's two bounds and receiver diagnostic, and the second
law's physical bound. Check their exact identities, source hashes, candidate,
timing, 800/400 receiver split and 239,867-packet training prefix.

Rebuild only the training error operator and forecast tangent needed by the
missing second-law receiver bound. Verify that the recomputed point forecast
matches the saved coordinates and native before-cast training difference.
Do **not** call the optimizer or start a new fit. The first-law results and
second-law physical bound are reused, not recomputed to improve them.

Save the second receiver bound and a comparison of both law-specific bounds
before opening the withheld receiver input. Only then score the 400 later
receiver positions. Keep the physical-aircraft truth unavailable and every
scientific decision at abstain. The resulting score is a development result,
not calibrated coverage or an independent Earth-model confirmation.

## Qualification, budget and recovery

First prove the continuation on the already completed short generated control:
hide its saved second-law receiver bound from the continuation code, rebuild
it from the saved fit/forecast, and compare the resulting bound and score with
the original sealed control. Test changed hashes, changed forecast points and
attempted early withheld access. Freeze the new worker source and environment.

After qualification, use one worker and one thread. The real continuation has
one initial start with at most **2,500,000 native calls**, **10 billion
packet/query visits** and **four hours** of cooperative wall time. If a reboot
interrupts that charged start, a separately frozen recovery may make at most
one more start with the same per-start limits. The total technical ceiling is
two starts, 5,000,000 native calls, 20 billion packet/query visits and eight
hours. Recovery may never repeat a sealed result or a completed numerical
failure. Both allowances are separate from the parent task's exhausted charge.
If the continuation exhausts its allowance, preserve the outcome and diagnose
it without enlarging the run. The seven reserved ESA confirmation groups
remain unopened.

[Parent outcome](DIAGNOSIS.md) · [original frozen plan](PLAN.md).

## Implementation steps

1. Add `analysis/lll/prediction_observed_continuation.py` with a pure saved
   artifact binder. It must reject mismatched parent hashes, law names,
   forecast points, candidate identities and split lengths. Test it with
   altered artifacts before running native code.
2. Add a continuation calculator in the same shared module. Reconstruct the
   fixed training error problem from the original training inputs, run a
   no-fit tangent forecast at the saved point, check the saved coordinates
   and native training difference, then calculate only the missing receiver
   bound. Compare against the completed generated smoke artifact.
3. Add a small `lll.studies` adapter and source-bound tests. Its task must
   bind the parent manifest and selected artifacts, save the missing bound and
   both interval unions before accessing the staged withheld receiver input.
   Prove an interruption/recovery cycle with the existing study engine.
4. Freeze the real definition and finite allowance only after those checks.
   Run once, verify all seals and charges, publish the actual withheld score
   or technical abstention, and update the roadmap. Keep the parent failure
   immutable.

The saved-artifact binder, no-fit forecast guard and native point-law adapter
pass seven focused software checks. A [source-bound generated check](continuation-smoke-equivalence.json)
rebuilt the missing receiver bound from the sealed fit and forecast with
**zero refits**. The bound, receiver diagnostic, both law unions and withheld
score matched the original sealed control exactly. Generated withheld rows
were opened only after both unions were saved. The check charged 1,047 native
calls and 4,646 packet visits in one thread. The final frozen worker smoke
completed **1/1 task**, matched the sealed control's bound, unions and score,
and retained zero refits and zero protected reads. Its core source hashes
match the current adapter. Task-level interruption-recovery qualification is
the remaining gate before the separate real-recording allowance can launch.
No real continuation has launched.

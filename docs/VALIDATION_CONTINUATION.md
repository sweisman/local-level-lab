# Complete the interrupted validation without repeating saved fits

The original validation stopped after a host reboot. Its frozen rule required
an uninterrupted cohort, so that run remains **interrupted**, regardless of the
results of later work. It saved 3,750 passing fits with zero recorded fit errors.
Four charged fits stopped mid-calculation and 590 were not started. The saved
fits include 155 complete, preassigned 24-fit seed families.
The read-only planner has verified all 3,750 saved result artifacts and produced
a fixed 594-task continuation inventory. The recovery and reporting code has passed 42
focused checks, including an abruptly exiting worker, a fresh command reading
its saved state, duplicate-lock refusal, source-change refusal, disk-reserve
enforcement and preservation of completed failures. A separate read-only audit
matched all 260 frozen sources and the real 594-task inventory.

The first technical release stopped after 93 charged fits. Ninety-one hit a
stage-deadline adapter error; two stopped under the failure-budget rule. The
terminal stage and its charges are sealed. These software errors are not
scientific model outcomes, and the original 3,750 saved fits remain unchanged.
The corrected adapter passes a regression test that reproduces the deadline
mismatch. A separate second release passed its one-fit gate and completed the
remaining 593 fits. All 594 continuation fits passed. The combined, independently
replayed [saved-data report](prediction-validation-continuation/README.md)
finds that all 4,344 prescribed fits passed and produced complete forecasts.
None of the 181 preselected simulated cases exceeded the fixed error limit or
was unavailable. The one-sided 95% failure upper bound is 1.64%, below the
declared 5% target. This validates the generated-data procedure under its
stated conditions; it does not establish aircraft error coverage or Earth-model
significance. After verification, the user service was disabled and removed.

The frozen evaluator requires the complete original task matrix even when a
stage runs only a subset. The continuation adapter supplies that unchanged
matrix and source/input context while each new stage owns only its own charges
and artifacts. A metadata check against the real 4,344-task evaluator passed
with a one-task stage and the fixed threshold 27.660528045730125. This check
performed no fit. The separate process test loads the adapter from a frozen
stage copy, matching the production worker's import path. The restart path also
honors a stage's scientific failure-budget stop.

## Recovery study

1. Verify the original manifest, environment, charge journals, result seals and
   artifacts. Bind their hashes in a new, separately named continuation plan.
2. Prepare exactly 594 tasks: the four interrupted identities and the 590
   unstarted identities. Keep every original seed, model, starting point,
   numerical method, fit limit and fixed calibration threshold. Preserve the
   original four charges. The four interrupted optimizations start again from
   their prescribed initial state because no complete optimizer-state checkpoint
   exists. Do not rerun any of the 3,750 completed fits.
3. Before numerical launch, qualify a finite task-level recovery mechanism with
   worker-loss and host-reboot controls. It must seal completed outcomes,
   including unsuccessful ones, and reassign only technically interrupted work
   under separately charged finite limits. It must prevent duplicate workers,
   enforce the original scientific limits and stop at its declared deadline.
   A notebook reboot is an expected interruption: after restart, the operator
   runs one idempotent resume command that verifies hashes, journals and leases
   before scheduling work. No calculation may depend on uninterrupted uptime.
4. Freeze the new continuation's source, inputs, environment, task list,
   recovery limits and acceptance rules. Run only after the qualification
   passes. A scientific failure is a final outcome, never a retry candidate.
5. Audit the original and new evidence together. Require exactly one final
   outcome per original task identity, all 181 complete seed families, complete
   provenance of the four technical re-executions and the original calibrated
   threshold. Report the original interruption and the successor result
   separately; do not describe the original run as having passed.

This is a disclosed recovery analysis specified after the interruption. It
preserves the substantial saved computation, but it is not the original
uninterrupted preregistration. Any formal coverage statement must say so and
pass the full combined validation criterion before being made.

## Frozen finite execution

The second release ran one prescribed fit first. Only a passing fit
unlocked the remaining 593. Together they covered the four previously interrupted
fits and 590 never started. At the measured rate of the saved validation, this
is roughly 14 hours of four-worker computation after the one-fit gate.
Freeze a maximum of 16 attempts per task and 128 technical interruptions in
total, including the original four; these caps allow at most 718 new charged
starts if the notebook repeatedly reboots. Keep the original 35 GiB free-disk
reserve and use a seven-day wall allowance so downtime does not require a
changed scientific procedure. Each stage uses at most four one-thread workers.

Preparation started its seven-day wall clock, copied and bound the verified
parent sources and inputs, and ran no fits:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.validation_resume prepare \
  --parent data/prediction-validation-host-20261030 \
  --plan data/ilvis0-source-point-development/validation-continuation-plan-20261109.json \
  --output data/prediction-validation-continuation-v2-20261109 \
  --max-attempts-per-task 16 --max-technical-interruptions 128 \
  --maximum-wall-s 604800 --smoke-task-count 1
```

The following command was the idempotent restart path. It audits the original results
and all completed stages before doing new work:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.validation_resume resume \
  --output data/prediction-validation-continuation-v2-20261109
```

Completion of the 594 fits established a complete combined task record. The
separate saved-data report applied the unchanged calibration threshold to all
181 families and passed the declared coverage rule. The restart receipt alone
makes no statistical coverage claim.

The read-only combined reporter was used after the campaign sealed every
outcome. It can replay and publish with:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.validation_combined_report
```

Independently replay the publication after it is written:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.validation_combined_report --verify
```

It checks the original and continuation seals, selects exactly one final
outcome per prescribed fit, and applies the fixed calibration to every
preselected simulated case. It rejects a changed combined completion receipt
and publishes atomically, so an interrupted write cannot expose a partial
public page. The publication preserves its reporting and runtime source files,
artifact hashes and numerical environment; `--verify` recomputes the result
from saved evidence. It cannot publish a partial campaign.

[Current status](HOST_PREDICTION_STATUS.md) ·
[Recovery rules](TASK_RECOVERY_AND_RETENTION.md).

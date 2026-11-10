# Recover unfinished work and clean up afterwards

**Required before any new long-running release.** Keep completed results, recover
only unfinished technical work, and remove unnecessary working files after the
campaign has closed and its evidence has been verified.

The completed calibration and interrupted validation keep their existing frozen
rules. Their records cannot be rewritten retroactively. A new release may cite
their verified saved results, but must state explicitly what those results can
and cannot establish. A reboot or worker loss must not make the next multi-day
campaign discard its completed calculations.

## Reuse completed work

Give each scientific task a permanent identity tied to its inputs, random seed,
model, prescribed starting point, numerical method and environment. Reuse its
sealed completed result, including an unsuccessful numerical result. Do not run
it again to seek a better answer.

A technical interruption may receive a new, separately charged execution attempt
only under recovery limits declared before the campaign starts. The original
attempt and all its charges remain recorded. Keep the same scientific inputs,
seed, method, bounds and acceptance rules. Cap both recoveries per task and
recoveries for the whole phase; do not reset the original wall allowance.

Recovery must use execution evidence, never whether a partial result looks
promising. Missing process handles or files alone do not establish that a worker
has stopped. Verify ownership and interruption before assigning replacement work.

Exhausting an evaluation budget, failing to converge or failing a scientific
check is a completed numerical outcome, not a technical interruption. None
becomes eligible for a recovery attempt.

## What a checkpoint can recover

Start with recovery between complete tasks. An interrupted task can be recomputed
from its original prescribed starting state under its separate finite recovery
allowance. This preserves the completed work elsewhere in the campaign.

Resuming inside an optimization requires more than saving its latest parameter
values. It needs a complete, tested optimizer-state checkpoint. Do not claim that
capability until it has been independently qualified.

## Keep files until verification, then clean up

| Files | Retention |
|---|---|
| Retained original measurements, selection records, seeds, settings, code and environment bindings | Keep permanently, with compression where appropriate. |
| Final fits, forecasts, scientific checks, attempt charges, failure records and required diagnostic evidence | Keep in the verified evidence archive. |
| Checkpoints and partial working files needed for recovery | Keep while work remains unfinished. Preserve necessary failure evidence when closing. |
| Superseded checkpoints, recreatable scratch files and duplicate working copies | Remove after closure and evidence verification, using an explicit inventory. |

Cleanup applies after an audited closure whether the scientific campaign passes
or fails. It must not erase an unfavorable result. Use the existing hash-verified
archive and compaction tools for evidence copies. True scratch files may be
discarded only when their purpose and reconstruction source were declared.

Delete only named, hash-checked files owned by the study. Never sweep directories,
follow symlinks, touch unfamiliar files or remove retained originals. Keep a
cleanup receipt listing what was removed and why. A failed archive or integrity
check blocks cleanup.

## Qualification before use

Implement this through the shared `lll.studies` lifecycle, not a copied worker.
Keep new development outside the running release's frozen dependencies. Test
duplicate-worker prevention, unchanged inputs and environment, charging before
execution, completed-failure preservation, recovery-cap exhaustion, original
deadlines and safe cleanup.

Then use finite generated-data controls to compare interrupted/recovered tasks
with uninterrupted tasks under the same numerical method. Include a host-reboot
or equivalent worker-loss test, as well as duplicate-worker exclusion. Use
cooperative test stops; do not signal or kill processes. Freeze the qualified
policy in each new long-running release before numerical work begins. If the
recovery path has not passed, do not launch that release.

[Current run](HOST_PREDICTION_STATUS.md) ·
[Execution controls](execution-recovery/README.md) ·
[Reproducibility](REPRODUCIBILITY.md).

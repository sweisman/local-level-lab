# Finite forecast-sensitivity check of saved numerical corrections

This is a **development diagnostic**, not a revised fit or an Earth-model
decision. The completed twenty-group study remains unchanged. Select three
failed fresh probes by the minimum, median and maximum *actual cost change*
in the saved stopping audit. Their identities are:

| Position | Saved fit identity |
|---|---|
| Minimum | `bb8061a43b4f14b6262ceda1-outer-0-header_elapsed-1` |
| Median | `a6e658d1550299e4eb9f00a3-outer-0-header_elapsed-1` |
| Maximum | `fad74da3a09951b31e882472-outer-0-header_elapsed-0` |

The selection depends on observed **numerical stopping behavior**, so these
three cannot validate an independent failure rate. They cover a useful range
for diagnosing whether a small training cost change hides a large later
path change.

For each task, take the exact saved training prefix, full IMU increments,
original fitted parameters and original forecast from the sealed study. Take
the reconstructed bounded correction from the source-bound saved diagnostic.
Rebuild the same training problem and calculate **one** candidate forecast
through the same native kernel. Keep every future receiver *position* absent
from the new study inputs. Compare the two predicted paths at the same fixed
times, reporting north/east/up RMS and maximum differences over the later
interval. Do not score either prediction against withheld positions.

Freeze the input hashes, source/environment hashes, three task identities,
three native calls, exact packet-visit allowances, up to three one-thread
workers, one-hour cooperative wall limit and separate finite interruption
allowance. Qualify task-level reboot recovery before launch. Preserve failures;
no alternate start, retry of a sealed failure or allowance expansion is
permitted. A completed diagnostic is evidence about numerical forecast
sensitivity only. Independent generated known-answer controls and a newly
frozen observed study remain necessary before changing any stopping rule.

## Interruption recovery

The initial three-task study allows one charged native forecast per case and
one hour of cooperative wall time. Its launcher uses three workers with one
numerical thread each. The existing task-recovery software qualification in
`remaining-recovery-request.json` and `remaining-recovery-tests.xml` passed
five source- and environment-bound interruption checks; recheck those exact
bytes before preparing any continuation.

If a reboot interrupts the initial run, first verify that the original
coordinator and all shard leases have exited. Close the original with
`lll.studies.task_resume close-original`; do not relaunch it. Prepare a
separate continuation with at most **two charged attempts per task across
both studies**, at most **three technical interruptions total**, one further
hour of cooperative wall time, and a **5 GiB** free-space floor. Its
`resume` command checks frozen source, inputs, environment, charges and
sealed outcomes and schedules only unfinished tasks. A sealed numerical
failure remains a failure. At most six native forecast attempts can be
charged across the original and continuation together.

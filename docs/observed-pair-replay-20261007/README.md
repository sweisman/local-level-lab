# Testing the partial Chicago–Los Angeles design through the full pipeline

This development replay asks whether the promising stationary-globe-versus-disc design
survives simulated IMU measurements, preprocessing and recovered orientation. It does not
establish a decision error rate or hardware performance.

**Complete:** all six analyses converged, retained 99 cruise minutes and passed the
stationary-globe/disc pairwise geometry gate under both wind treatments. All decisions
abstained; the full three-model gate still fails. Residual-based uncertainty is much larger
than the planning assumption. Read the [results and next step](SUMMARY.md).

The recorded position window starts one hour after the first Chicago–Los Angeles fix and
lasts two hours. The IMU turns at minutes 5, 15, 30, 40 and 90 within that window. Between-fix
motion is assumed by C2 interpolation; missing positions remain unsupported. The ground
path stays fixed while wind and mixed sensor drift are injected.

Six analysis attempts are authorized: three physical-model truths, each analyzed with the
broader wind candidate and the physical wind/airspeed candidate. All use the same new
development seed, 600910, to make the candidate comparisons matched. These six tasks are
not six independent draws of a null distribution. The matched forward-reference method
recovers orientation from the simulated measurements. Supplied design axes are not used
as recovered axes. Full nonlinear fitting and pairwise profiles are enabled; bootstrap is
zero because this pilot tests geometry and processing before calibration or power studies.

The source, policy, configuration and numerical environment are frozen. Two workers each
use one numerical thread. Started attempts, including failures, are spent and are not retried.
The existing runner saves fsynced per-shard journals and merges with duplicate/provenance
checks. A detached coordinator can survive a terminal or chat disconnection.

Documented corpus:

| Artifact | Purpose |
|---|---|
| `plan.json` | Frozen six-task plan and source/configuration/environment identities. |
| `preparation-review.json` | Authorization, buffered turn checks and task identities. |
| `review.json`, `noise-review.json`, `residual-decomposition.json`, `verification.json`, `SUMMARY.md` | Completed fit/geometry review, noise and motion decomposition audits, independent input checks and interpretation. |
| `run/plan.json`, `run/launch.json`, `run/status.json` | Bound plan, durable launch and coordinator state. |
| `run/shard-000.jsonl`, `run/shard-001.jsonl` | Append-only task starts and completed outcomes. |
| `run/shard-000.status.json`, `run/shard-001.status.json` | Worker progress. |
| `run/coordinator.log`, `run/shard-000.log`, `run/shard-001.log` | Worker output for diagnosing interruptions. |
| `run/diagnostics/<task_id>/` | Explicit task-linked preprocessing/fit arrays, metadata and generated plots. |
| `run/campaign.json`, `run/merge-status.json` | Duplicate-checked merged results and completeness. |
| `run/*.lock`, `run/*.recovery.jsonl` | Worker exclusion and preserved truncated writes, when needed. |

Check coordinator and shard status before any resume; never start a duplicate or edit
scientific source while workers are active. Resume the same plan with the same total limit
of six; completed attempts are skipped and an interrupted started task becomes a preserved
failure. Launch outside the per-command sandbox so detached processes survive tool exit.
This run is complete: do not resume it or rerun any completed attempt.

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/sharded_campaign.py run docs/observed-pair-replay-20261007/plan.json --output docs/observed-pair-replay-20261007/run --attempt-limit 6 --workers 2 --detach
```

Report processing failures, retained cruise/headings, recovered-axis uncertainty, magnetic
exclusions, nonlinear convergence, design contrasts and pairwise abstentions separately.
No empirical decision artifact, calibration, independent validation or production promotion
is authorized by this replay. Further flight attempts require their own scope authorization.

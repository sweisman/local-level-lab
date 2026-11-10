# Study execution and recovery

**Initial recovery qualification passed all 61 software checks, including 26 new
recovery tests.** The checker reads existing records and recommends what may happen next. It does
not start calculations, retry lost work or change results.

The checks cover:

- Interrupted starts on different workers, including loss of both starts of a
  required calibration setting.
- Held locks, changed source or input files, damaged journals, altered results
  and the original deadline.
- Completion during a status check and fully archived completion records.
- Preservation of charges and files: inspection creates no starts, clock,
  journal or replacement result.

Use the existing [status command](../../analysis/STATUS.md):

```sh
~/venv/bin/python analysis/status.py --study data/prediction-calibration-feasible-20261028 --recovery
```

The closed calibration is reported as **closed**, even after recoverable working
copies have been compacted. An owned lock means work is reserved; it does not
identify the process or prove that it is still computing. For unfinished work,
the shared runner must still check the complete evidence before launching any
uncharged task.

## What this establishes

The test report is bound to 174 source files and the numerical environment.
The [qualification report](qualification-report.json),
[source binding](qualification-request.json) and
[test results](qualified-tests.xml) preserve that evidence. These are bookkeeping
checks, with no aircraft observations, optimizer starts or native model calls.

## Launcher exit tests

The [command-sandbox attempt](../execution-command-sandbox/README.md) produced
no worker task or heartbeat after its launcher returned. It remains closed.
The [separate host-service test](../execution-host-service/README.md) passed:
another command observed the worker running, then verified all eight heartbeats
and its sealed completion after 16.1 seconds. It used one metadata task start
and zero model evaluations. Source and environment bindings match.

The host service therefore provides an execution arrangement that survives a
normal submitting command's exit. It does not establish survival of a host reboot,
container reset or user-manager shutdown after logout. Unsaved optimization
state still cannot be recovered by restarting a process.

The [execution-recovery plan](../CALIBRATION_RECOVERY_PLAN.md) now proceeds to
preparing a fresh finite release. The interrupted campaign remains closed; its
1,813 completed forecasts supply no calibration threshold.

The [fresh release qualification](../host-calibration-preparation/README.md)
passes 154 checks. Three additional recovery tests cover its explicit rule that
even one interrupted charged start blocks continuation of calibration or
validation, while a completed unsuccessful start retains the original repeat
selection rule.

## Launching a future approved study

Prepare and verify the study first. Check its leases and recovery advice with
the status command. A host user service can then own the existing shared runner,
using a unique service name and the actual absolute repository path:

```sh
systemd-run --user --unit=lll-UNIQUE_STUDY_ID --collect \
  --property=Restart=no \
  --property=WorkingDirectory=/absolute/path/to/local-level-lab \
  --setenv=PYTHONPATH=/absolute/path/to/local-level-lab/analysis \
  "$HOME/venv/bin/python" -m lll.studies \
  --root /absolute/path/to/local-level-lab \
  run data/UNIQUE_STUDY_ID --reserved-threads 0
```

This is a template, not an additional allowance or permission to restart a closed
study. The frozen runner sets the worker/thread allocation and cooperative limits.
Keep the host and its user service manager running. Automatic service restarts
are disabled; a real interruption still leaves its starts charged.

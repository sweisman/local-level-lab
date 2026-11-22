# Refit a recorded control from the evidence package

This check repeats one archived IMU8 fit from extracted source and input files
in an isolated working directory. The control uses 445 training receiver
epochs. Its forecast receives later timestamps and inertial increments only.
The required tolerance is exact byte equality for the fit, forecast and native
compilation records. The original fit and its study remain sealed.

The [toolchain record](portable-refit-toolchain.json) pins the local Python,
C and C++ executable hashes and the historical runtime environment. Preparation
also checks compiler versions against the historical build. The final check
compares the rebuilt binary hashes and compiler flags. Package verification and
extraction work on other systems. The declared refit requires the pinned
environment.

Run these commands from a copy of the repository with the package available.
Choose a fresh output directory for the first extraction.

```sh
refit_dir=data/ilvis0-nasa-portable-refit-v1-20261118
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.portable extract-parts \
  docs/ilvis0-matched-trial-observed-runtime/refit-parts "$refit_dir" > /tmp/lll-refit-extraction.json
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_portable_refit prepare "$refit_dir"
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_portable_refit run "$refit_dir"
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_portable_refit check "$refit_dir"
```

The refit has one start, 30 logical evaluations, at most 61 native calls and
a cooperative 20-minute wall limit. It uses one numerical thread. Account for
any other jobs with `--reserved-threads` on both the guard and the run command.
The study writes its journal under
`$refit_dir/source-freeze/data/portable-imu8-control`. Once saved, a completed
outcome, including a numerical failure, stays sealed. An interruption before
a recorded start can continue within the original allowance. An actual
interrupted start may be recovered once under a separately charged allowance
with the same limits and the qualified shared task recovery procedure. The
initial charge ledger is preserved.

This is a numerical reproduction of one control. It provides no new aircraft
observations and no estimate of the frequency of model preferences.

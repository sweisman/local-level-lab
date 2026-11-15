# Fit-adjusted control: recovery command

The source-frozen two-recording control lives at
`data/esa-fit-adjusted-control-v1-20261115`. Its recovery policy is
`qualification/fit-adjusted-recovery-policy.json` in this directory.

From the repository root, use the same idempotent command after an interruption:

```sh
env LLL_STATUS_ALLOCATIONS_ONLY=1 PYTHONPATH=analysis \
  /home/sweisman/venv/bin/python analysis/tests/run_numerical.py \
  --workers 2 --threads 1 --reserved-threads 0 -- \
  /home/sweisman/venv/bin/python -m lll.esa_fit_adjusted_control_recovery resume
```

The allocation-only setting makes the recovery wrapper check live numerical
thread ownership without scanning completed historical studies. The wrapper
verifies frozen hashes and charges, reuses sealed results, and resumes only
unfinished work within its separate finite recovery allowance. Do not start a
second worker while the first owns the study lock. Check the study with:

```sh
/home/sweisman/venv/bin/python analysis/status.py \
  --study data/esa-fit-adjusted-control-v1-20261115
```

This is a generated-data software control. It makes no Earth-model decision and
does not open reserved ESA confirmation flights.

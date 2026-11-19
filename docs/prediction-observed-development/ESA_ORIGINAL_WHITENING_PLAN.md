# Score calibration changes with the original ESA training weights

Rebuild the original fixed training covariance for each of the three
sealed profiled-removal, increment-error fits on recording 187. Use
only the 400 training reports and their inertial prefix for these
covariance calculations. Match the archived covariance identity and
reproduce the nominal whitened residual vector exactly. Save the
numerical innovations factors in a hash-bound, compressed artifact
and verify that restoring the factor artifact gives identical results.

For each model, score the two already selected calibration shifts from
the [earlier-fit cost check](ESA_EARLIER_FIT_COST_RESULT.md). Evaluate
their propagated positions with the original fixed weights and report
the actual training-loss increase, its linear estimate and whether
the increase exceeds the corresponding sensitivity allowance. Verify
that the exact result is within the previous white-covariance interval.
The result describes sensitivity under the archived error law.

The study allows three tasks on three one-thread workers. Each task can
compile one noise bridge and execute at most 120,268 noise-kernel calls
and three scalar value sweeps. The main allocation has a 420-second
cooperative limit. There are no optimizer starts and no receiver reads
after the training cut or from reserved flight groups.

The shared recovery qualification is run before launch. If interrupted,
the recovery launcher verifies the saved results, exclusive ownership
and prior charges before allowing new work. Only unfinished tasks can
get a separate allowance, with at most one technical interruption and
at most two starts for any unfinished identity. The recovery campaign
has its own 900-second wall limit and 1 GiB free-space requirement.
Completed tasks and failures stay sealed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.esa_original_whitening qualify-request
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m pytest -q analysis/tests/test_task_resume.py \
  --junitxml=data/esa-original-whitening-v1-20261118-qualification/tests.xml
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.esa_original_whitening prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-original-whitening-v1-20261118 --reserved-threads 0
```

After an interruption, use the original allocation and the verified
`lll.studies.task_resume` launcher. Close the interrupted original,
prepare the single recovery campaign from its terminal ledger, then
resume that campaign. Use the original study directory as `--parent`,
`data/esa-original-whitening-v1-20261118-recovery` as `--output` and
`data/esa-original-whitening-v1-20261118-qualification/request.json`
as the qualification request. The preparation flags are
`--max-attempts-per-task 2 --max-technical-interruptions 1 --maximum-wall-s 900 --minimum-free-bytes 1073741824`.
Once the recovery campaign exists, run only its `resume` command.

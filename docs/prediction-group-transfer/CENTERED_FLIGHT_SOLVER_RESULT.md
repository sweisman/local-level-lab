# The centered solver hit its time limit in the generated flight test

On the first generated flight, the existing trust-region solver passed the
numerical and withheld-position checks in **10 training evaluations**. The
centered L-BFGS-B solver on the same input attempted **182 training
evaluations** before the study's 210-second limit. It saved no final fit or
forecast. Consequently, no matched pair qualified.

| Generated fixture | Trust region | Centered L-BFGS-B |
| --- | --- | --- |
| Specified-field globe, header clock | Passed both checks | Time limit before final fit |
| Zero-field globe, nominal clock | Unstarted | Unstarted |
| Disc, header clock | Unstarted | Unstarted |

The saved trust-region fit gives a lead for diagnosis. At that point the
largest normalized Jacobian column, initial X velocity, is about **275,000
times** the smallest column, Z gyro bias. The centered objective removes
an irrelevant cost offset while leaving those parameter scales unchanged.
The spread is a reason to test scaling on saved generated problems before
another native comparison. It does not identify the cause of any specific
accepted or rejected step in the unfinished fit.

The manifest and charges are closed. The run recorded two results out of
six planned starts and used no aircraft data. It leaves the existing solver
in place. The [known-optimum check](CURVED_BOUNDED_SOLVER_RESULT.md) remains
valid for its four generated surfaces and eight starts per method.

## Reproduce the saved checks

With the closed `data/centered-flight-solver-v1` study restored, summarize
the sealed fits and journaled operations without running a new fit.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.centered_flight_solver_study report
```

[Frozen plan](CENTERED_FLIGHT_SOLVER_PLAN.md) ·
[Six dispositions and scale diagnostic](centered-flight-solver-result.json)

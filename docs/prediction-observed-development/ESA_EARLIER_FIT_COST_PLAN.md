# Match calibration changes by earlier fit cost

Use the same three saved fits and the larger combined rays from the
[mixed calibration check](ESA_MIXED_CALIBRATION_RESULT.md). The archived
earlier residuals and Jacobians specify the original standardized training
loss. Choose the farthest step on each ray with an increase of at most
0.001 or 0.01 in that squared loss under the affine approximation. Stop
at the original 0.10 parameter cap if the allowance is larger than the
increase at the cap. Both values are sensitivity scales.

Propagate the two steps and the nominal point with the frozen scalar
integrator. Use the original independent receiver white covariance as
a lower bound on the full training covariance. In the exact same
coordinate chart, the full whitened norm of any position change is no
larger than its white-covariance whitened norm. Apply the triangle and
reverse triangle inequalities to bound the actual change in training
loss. Record whether that entire interval stays below the specified
allowance. This bound assumes the archived covariance components and
does not certify their accuracy on aircraft.

Report earlier and later position displacement in metres. Use only the
400 earlier receiver reports, the sealed model predictions and the
inertial measurements through the later query times. There are three
tasks with three value sweeps each, no refits, one thread, and a
120-second cooperative wall limit. No withheld receiver reports or
reserved flight groups are opened.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_earlier_fit_cost prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-earlier-fit-cost-v1-20261118 --reserved-threads 0
```

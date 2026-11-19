# Check finite calibration changes against the ESA forecast tangent

Use the single passing [fixed-fit replay](ESA_NATIVE_TANGENT_REPLAY_RESULT.md)
on ESA recording 187. Take the three weakest directions of the saved
whitened training Jacobian. For each, choose the sign with greater available
distance inside the original normalized bounds. Test steps of 0.01 and
0.10 along that ray. Reject steps that would leave the allowed range.

Run the scalar long-double integrator derived from the original frozen
source. Check that its nominal prediction matches the sealed tangent
prediction to within one micrometre at every query before testing the
six changes. Compare the scalar path displacement with the tangent's
prediction in north, east and height metres. Report RMS and peak departure
separately for the 400 earlier queries and 120 later queries.

The freeze permits one nominal and six perturbed value sweeps, one thread,
a 120-second cooperative wall allowance, and zero optimizer starts. Only
the original increment stream, earlier receiver observations and saved
predictions are used. No later receiver positions or reserved flights are
opened. The six sampled directions and sizes do not establish a bound over
all admissible calibration changes.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_tangent_remainder prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-tangent-remainder-v1-20261118 --reserved-threads 0
```

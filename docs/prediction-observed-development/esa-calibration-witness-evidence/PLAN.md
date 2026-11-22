# Check how far feasible calibration changes move the forecasts

The [previous upper bound](ESA_JOINT_FORCE_SUPPORT_RESULT.md) is larger
than the saved globe–disc separation. A feasible example can show whether
that reflects freedom in the saved calibration design or just a wide bound.
Use the same two zero-field forecasts, 400 earlier positions, 120
forecast epochs, fixed weights, calibration box and squared-loss increase
limit of 0.01. Assume zero earlier unshared error for this comparison.

For each candidate, make two numerical proposals with at most 200
iterations each. One lets all 51 coordinates vary in their boxes. One
uses only the 27 physical columns. Propose with a loss increase limit of
0.008 to leave room for an independent arithmetic check. Test each
original proposal at 0.999 of its displacement. Also test each proposal's
physical displacement at 0.999 times 1, 0.8, 0.5, 0.25 and 0.125, with
all 24 shared values evaluated from the same physical calibration at
each point. Verify all 12 points per candidate against the saved factors
using outward whitening and signed score intervals. Record each point
and its loss result, including failures.

Use two one-thread workers with a 150-second cooperative wall allowance.
Charge each proposal and its six checks in a separate journal entry.
The first freeze stopped before either proposal because its adapter
attempted to charge both proposals in one entry. Its terminal manifest
is `84d457848106968b7a6003939222af4ce7d9ca77f9915544d0bd6b6b46d76dc4`
and records zero bound calls and zero checks. The second freeze corrects
the accounting entry with the same inputs and numerical limits.
The work starts no trajectory fits and reads no later receiver positions
or reserved recordings. The linked examples evaluate the saved
calibration map numerically and test feasibility in the saved design.
They do not replay the full nonlinear flight integrator or bound omitted
earlier or later errors.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_calibration_witness
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-calibration-witness-v2-20261119 --reserved-threads 0
```

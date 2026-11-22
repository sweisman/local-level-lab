# Where X-axis bias can change the ESA direction result

With the other sensor corrections fixed, the globe has the smaller
directional error in all six settings for every X-axis bias from
**−0.10 to +0.0225 m/s²**. Each shape can still choose any retained
fraction of the specified background field. The bound covers values
between both grids.

The positive end of that guaranteed interval is **+0.0265 to
+0.0290 m/s²** with 11-report averaging and **+0.0225 m/s²** with
25-report averaging. The earlier exact replay still verifies the
disc preference at **+0.10 m/s²**. The interval check leaves the
transition between these results unresolved.

The ground stops cannot supply the needed bias limit. At +0.0225 m/s²,
adjusting the other accelerometer terms gives ground force half-ranges
of **0.0002055 and 0.0000953 m/s²**. That is close to the **0.0002046
and 0.0000911 m/s²** from the unconstrained shared ground correction.
These differences do not establish which calibration applies in
flight. The position check must address the whole remaining
positive-bias range to establish a joint result.

The calculation reproduced both existing endpoints and the nominal
observations, then evaluated 401 X values. It reused one integration
of the earlier packets and ran one ground linear program. Four
focused tests passed. No new Earth-model fit or reserved group was
opened. Receiver errors and changes in the other instrument terms
remain outside this one-axis bound.

With the sealed direction, ground and 400/120 artifacts in place, run
from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_direction_profile freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_direction_profile run
```

[Frozen plan](ESA_X_BIAS_DIRECTION_PROFILE_PLAN.md) ·
[Bias ranges, scores and hashes](esa-x-bias-direction-profile-result.json)

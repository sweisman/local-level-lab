# Nonlinear compensation at the edge of the X-bias range

The best exact trial at or above **+0.0225 m/s²** reduced the
specified-field globe's earlier horizontal error to **7.72 m RMS**
and height error to **0.25 m RMS**. Its increase in weighted squared
loss was still **5.948**, beyond the original allowance of **0.01**.
The RMS and weighted-loss figures answer different questions.

| Earlier position trial | Cost increase | Horizontal RMS |
| --- | ---: | ---: |
| Change only X bias to the boundary | 20,493.69 | 647.23 m |
| Allow the full affine correction | 6.152 | 9.51 m |
| Best of the two exact correction rounds | 5.948 | 7.72 m |

The nonlinear residual remainder was **0.453** in weighted norm
at the best point. The earlier affine calculation showed that a
remainder of at least **1.047** is needed to recover the allowance
anywhere in the positive range above the boundary. The observed
0.453 applies to the checked point only. A uniform upper bound at
other compensating parameters is still missing.

In the saved direction grid, the first point with a verified disc
preference is at **+0.049–0.050 m/s²** in the 25-report settings and
**+0.063–0.067 m/s²** in the 11-report settings. These are sampled
reversal points. They do not certify the globe in the gaps between
the end of its guaranteed range and the first observed reversal.

Seven integrator passes completed, including the saved baseline.
The original fit was left sealed. All six new points and both
local correction proposals are retained. No later receiver positions
or reserved flight groups were opened. Three focused tests passed.

With the earlier replay and affine range result in place, run
from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_nonlinear_range prepare
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-x-bias-nonlinear-range-v1 --reserved-threads 0
```

For the completed study, reuse its existing charged result.

[Frozen plan](ESA_X_BIAS_NONLINEAR_RANGE_PLAN.md) ·
[Exact replays and hashes](esa-x-bias-nonlinear-range-result.json) ·
[Prior affine bound](ESA_X_BIAS_RANGE_POSITION_RESULT.md) ·
[Saved direction grid](esa-x-bias-direction-profile-result.json)

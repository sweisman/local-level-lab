# Force direction would have to change rapidly to mask the gaps

The most favorable nonnegative gain cleared the training lower bound in all
48 profiles. Even after that correction, explaining the remaining upper-bound
gaps solely by direction change within packets would require the following
peak rates somewhere in the training data.

| GPS trajectory approximation | Range of necessary peak rates across profiles |
|---|---:|
| Quadratic | 3,072–3,292°/s |
| Fourth-degree | 1,836–2,394°/s |

These numbers refer to the direction of specific force in the instrument
frame. Aircraft attitude can change that direction, and so can changes in
the force itself. The calculation neither observes these rates nor
establishes a credible upper limit on them. It uses the most favorable
packet period permitted by each clock, including the 7.5 ms ceiling under
header timing.

With both GPS motions required to share one training gain, the fourth-degree
case had no later checks above its training rate threshold. The IMU8
quadratic case exceeded it in two later window–clock–track checks per
candidate. The joint profiles had no later failures of the lower bound
after holding their gains fixed. The thresholds are training maxima on two
recordings and do not establish statistical coverage.

This [saved-interval calculation](FORCE_DIRECTION_GAP_PLAN.md) isolates one
way a packet norm can differ from continuous force. It leaves other causes
open, including axis-specific calibration and receiver-path error.

[All 48 profiles](force-direction-gap-receipt.json).

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_force_direction_gap replay
```

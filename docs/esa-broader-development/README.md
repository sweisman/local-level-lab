# Three more development intervals

**The metadata rule selects four nonoverlapping twenty-minute ranges.** One has already been analyzed;
three are additional candidates. These all belong to the same ESA development group, not independent replications.

Take the first and last twenty minutes of each of the two eligible full-motion runs. The original receiver
inventory stays unchanged. No gyro value or model result enters the choice.

| Parent run | Part | Status | Receiver support indices |
|---|---|---|---|
| 1 | First twenty minutes | Already analyzed | 9036–11436 |
| 1 | Last twenty minutes | Candidate; not prepared | 42470–44870 |
| 2 | First twenty minutes | Candidate; not prepared | 49554–51954 |
| 2 | Last twenty minutes | Candidate; not prepared | 58525–60925 |

Indices identify original receiver records; they are not interpolated time estimates.
Each candidate keeps 800 earlier training queries and 400 later prediction queries.
Exact timing, IMU support, source hashes and trajectory summaries still need their own preparation checks.
No original recording is opened, and no fit or native calculation runs in this planning step.

Preparation and fitting wait for the preceding error-assumption assessment and their separately qualified
finite definitions. These ranges are not confirmation data. All seven confirmation groups remain protected.

[Selected ranges CSV](windows.csv) · [Selection rules](PLAN.md) ·
[Parent inventory](../esa-development-selection-v2/README.md) · [Next analyses](../NEXT_STEPS.md)

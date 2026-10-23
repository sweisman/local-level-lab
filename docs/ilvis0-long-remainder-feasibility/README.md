# Full-history prediction comparison

**0/6 endpoint targets passed; 6/6 numerical checks passed.**
The long-history prediction method remains unqualified.

These are generated software cases. They test the prediction-bound method,
not which physical model the aircraft measurements support. Passing requires
both the numerical checks and useful ranges: at most 20 m north, 20 m east
and 50 m in height. A wide range fails even if it contains the known answer.

| Candidate | Removal assumption | Previous N / E / height, m | New N / E / height, m | Outcome |
|---|---|---|---|---|
| Globe, specified field | None | 2,026,649.137 / 2,413,285.898 / 1,462,689.868 | 906,758.55 / 993,975.357 / 551,717.445 | Checks passed; ranges too wide |
| Globe, specified field | Profiled | 2,024,544.207 / 2,418,668.61 / 1,460,978.993 | 909,365.068 / 1,002,386.657 / 560,955.345 | Checks passed; ranges too wide |
| Globe, zero field | None | 1,704,083.361 / 1,995,604.662 / 1,258,779.766 | 784,192.262 / 843,224.274 / 464,058.903 | Checks passed; ranges too wide |
| Globe, zero field | Profiled | 1,699,789.611 / 2,001,862.405 / 1,252,963.338 | 781,586.401 / 847,104.216 / 463,597.147 | Checks passed; ranges too wide |
| Flat disc | None | 657,256.186 / 109,307.419 / 312,764.814 | 533,332.73 / 83,775.835 / 226,849.086 | Checks passed; ranges too wide |
| Flat disc | Profiled | 687,523.048 / 114,908.395 / 339,268.037 | 560,561.517 / 88,964.463 / 248,662.948 | Checks passed; ranges too wide |

Displayed widths are rounded for readability; the sealed results preserve
their full precision. Rejected or incomplete cases remain in the table.
The calculation reuses the saved training observations, constraints and
baseline trajectory values and Jacobians. It changes neither the physical calibration limits nor
the original shared-coordinate normalization.

The closed comparison records 6/6 completed outcomes and
6 reserved bounds over 3.70 wall hours.
There are no new aircraft fits or baseline trajectory-oracle queries;
the interval-bound source streams are recomputed.

The 53-stretch model comparisons are unchanged. Even a complete endpoint
pass would leave whole-period coverage, numerical treatment and the aircraft
observation-error model to be qualified before new withheld-position fits.

[Method and limits](PLAN.md) ·
[Original long-history result](../ilvis0-long-staged-feasibility-v2/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Reproducibility](../REPRODUCIBILITY.md).

# Four-group forecast-error transfer

**3/4 groups** have second-cut north, east and height RMS errors within the fixed three-recording development reference.
3/4 pass the separate fixed physical prediction screen; 1/4 cannot be scored because the second-cut fit did not pass its numerical check.

| Recording | IMU | Latitude | Duration | Second-cut result | Within reference | Physical screen |
|---|---:|---:|---:|---|---|---|
| `b365bdf3…` | 8 | -63.1° | 9.75 min | abstain_both | — | — |
| `b4ab6e12…` | 21 | 75.3° | 6.88 min | abstain_inner | yes | yes |
| `c16df82d…` | 21 | -63.7° | 10.80 min | matched | yes | yes |
| `2f7e37c4…` | 21 | -60.9° | 9.42 min | abstain_inner | yes | yes |

The reference is the maximum earlier forecast error from three prior
development recordings under one declared clock and processing case.
It is **not a confidence interval**. Four retrospective groups cannot
establish a rare failure rate, calibrated Earth-model significance or
the gyroscope channel’s separate contribution. A fit can remain a
numerical failure even when another start looks promising. No result
here changes the saved 53-stretch shape comparison.

[Every group and direction](result.csv) · [All starts](fit-audit.csv) ·
[Source selection](selection.csv) · [Fixed method](OBSERVED_PLAN.md) ·
[Recovery procedure](RECOVERY.md)

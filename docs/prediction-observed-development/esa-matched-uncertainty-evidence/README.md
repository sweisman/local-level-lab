# The 800-report ESA forecast misses its height ranges from the start

At the common 120-report horizon, the nominal 95% height range contained
only **25 of 120** GPS positions after the 800-report cut. The three-axis
ellipsoid contained **37 of 120**. North and east were inside their own
ranges throughout. The adjusted point forecast passed all four
[position-error limits](ESA_MATCHED_CONDITIONING_RESULT.md), so the height
misses concern the stated uncertainty around that forecast.

| Earlier reports | Error law | Later reports | North / east / height inside marginal ranges | Inside three-axis ellipsoid | Peak squared distance in covariance units |
| ---: | --- | ---: | --- | ---: | ---: |
| 200 | Both | 120 | 120 / 120 / 120 | 120 | 1.36 |
| 400 | Both | 120 | 120 / 120 / 120 | 120 | 1.02 |
| 600 | Both | 120 | 120 / 120 / 120 | 120 | 0.86 |
| 800 | Increment | 120 | 120 / 120 / 25 | 37 | 39.79 |
| 800 | Point | 120 | Unavailable | Unavailable | Unavailable |

The ellipsoid admits squared distances through 7.81. At the 800-report
cut, the first 120 height errors had RMS **4.25 times** their stated
standard deviations after standardizing each position separately.

## Original longer horizons

| Earlier reports | Error law | Later reports | North / east / height inside marginal ranges | Inside three-axis ellipsoid | Peak squared distance in covariance units |
| ---: | --- | ---: | --- | ---: | ---: |
| 600 | Both | 200 | 200 / 200 / 200 | 200 | 0.86 |
| 800 | Increment | 400 | 400 / 400 / 25 | 37 | 54.86 |

The full 800-report-cut result reproduces the [earlier coverage audit](CONDITIONAL_COVERAGE_RESULT.md).
All positions that fit the height range or ellipsoid were in the first
120. The later positions therefore worsen an undercoverage already
present at the common horizon. The two laws agree to the table's
precision wherever both have a saved forecast.

Ten charged checks completed. They compare the archived uncertainty with
the same GPS positions and treat fitted calibration as fixed. The results
share one development flight. No independent-flight coverage or decision
rate follows, and the seven reserved groups remain closed.

[Frozen plan](ESA_MATCHED_UNCERTAINTY_PLAN.md) ·
[Axis diagnostics for every case](esa-matched-uncertainty.json) ·
[Verified evidence bundle](esa-matched-uncertainty-evidence/replay.zip)

# Receiver offsets change across the ESA development flight

The first 97 windows predicted faster changes in the receiver position
differences reasonably well over the following 98 windows. They
underestimated the changes in window-wide offsets, especially late in
the flight. Every window had all 120 reports from all three GPS solutions
after matching to the fixed integer-second grid.

| Later batch | Windows | Window offsets | Slow changes | Middle band | Fast band |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 25 | 3.04 | 0.53 | 0.71 | 0.91 |
| 2 | 25 | 7.27 | 1.27 | 0.68 | 0.84 |
| 3 | 24 | 17.33 | 1.10 | 1.11 | 0.95 |
| 4 | 24 | 71.13 | 5.20 | 1.06 | 1.02 |

The table gives mean squared standardized errors for the
separate-receiver model. Values around one indicate agreement with the
working variance scale. The unrestricted covariance gives a nearly
identical score for changing coefficients overall and a substantially
worse score on the offsets. The isotropic comparison predicts the
offsets better than either fitted covariance, but still underestimates
their size in the final batch by about 13 times in squared units.

The result identifies what a transferable error model needs to
address. Relatively fast variation and slow shifts in the positions
behave differently. The receivers share one antenna, so these
comparisons leave common GPS errors and absolute accuracy open.
The seven reserved flight groups stay closed.

The donor fit was sealed before the four later tasks were frozen.
All five tasks completed, six software checks passed, and no aircraft
fit ran. The study retained both stages and recorded 247 charged calls.

[Frozen plan](ESA_PPP_COVARIANCE_CHRONOLOGY_PLAN.md) ·
[Donor evidence](esa-ppp-covariance-chronology-train-evidence/README.md) ·
[Later evidence](esa-ppp-covariance-chronology-score-evidence/README.md)

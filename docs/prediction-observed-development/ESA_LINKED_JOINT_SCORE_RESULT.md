# Keeping the calibration constraints together lowers the bound to 53.04

The combined upper bound fell from **53.10 to 53.04 units** across the eleven
surviving calibration ranges. The forecast gap is **25.41 units**, so the
zero-field comparison remains unresolved over the full calibration range.

| Candidate | Ranges checked | Ranges tightened | Previous upper bound | New upper bound |
| --- | ---: | ---: | ---: | ---: |
| Zero-field globe | 5 | 4 | 20.649 | 20.637 |
| Zero-field disc | 6 | 4 | 32.456 | 32.401 |

The [fixed calculation](ESA_LINKED_JOINT_SCORE_PLAN.md) bounded the score
using all 60 coordinates together. It kept the 270 archived static
inequalities and the five checked training rows on each range. All eleven
ranges used the full allowance of eight proposals and seven additional
training rows. Each of the 88 proposed upper bounds passed both exact
arithmetic checks. For each range, the audit kept the smallest checked
bound or the previous bound, whichever was lower. All previously saved
feasible scores remained within the retained bounds.

Four disc ranges still have upper bounds above the entire forecast gap.
The largest is 32.401 units in child 1 of range 3/2. This is an upper bound
on a relaxed region. It leaves open whether any physically admissible
calibration could move the score that far. The full integration remainder
and aircraft error law remain open.

At the two highest disc ranges, all seven added rows left the certified
joint bound unchanged to four decimal places. The final proposed points'
earlier residual norms still exceeded the original radius by about 243
and 126, respectively. The linear relaxation can therefore assign high
scores to points well outside the full earlier loss constraint.

All eleven tasks completed in 148 seconds. The ledger contains 165 charged
operations, zero new trajectory fits and zero reserved-flight reads.
[Per-range bounds](esa-linked-joint-score-result.json)

[Source and execution receipts](esa-linked-joint-score-evidence/README.md) ·
[Verified reproduction bundle](esa-linked-joint-score-evidence/bundle.zip)

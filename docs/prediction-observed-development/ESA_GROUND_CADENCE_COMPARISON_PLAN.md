# Compare the two ground references at the same cadence

Use three already published signed range reports from ESA development flight
187. Freeze their SHA-256 hashes and use only the following disjoint blocks
on the GPS week clock.

| Block | First endpoint | Last endpoint | 30-second intervals |
| --- | ---: | ---: | ---: |
| Earlier | 388230 | 388530 | 10 |
| Later | 388620 | 388710 | 3 |

Sum the 30 one-second Qaqortoq range changes across each interval. Require
each retained satellite to appear in all 30 rows and in the permanent Nuuk
range report. Include an interval only if it has at least five matched
satellites. Use the ionosphere-free combination for Nuuk. Center all four
vectors over the same satellites per interval to remove the receiver clock
term. Report support, ground-to-ground disagreement and the difference
between the two archived aircraft residual calculations. For each station,
compare the paired aircraft residual before subtracting the ground residual,
after full subtraction and after multiplying the ground residual by a single
least-squares coefficient learned on the earlier block only.

The original Nuuk and Qaqortoq reports use different satellite products
and saved aircraft path calculations. Each correction is tested against its
own aircraft residual. Differences between the reports can include those
processing choices as well as geography, atmosphere and antenna effects.
The comparison describes one flight and cannot give an absolute aircraft
error bound or test the reserved flights.

This is a saved-data audit with one numerical thread and at most 390 input
intervals in the comparison. It runs no fits, makes no new receiver solution
and opens no reserved recordings.

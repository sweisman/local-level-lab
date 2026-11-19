# The surviving ESA ranges still permit large forecast changes under the relaxed constraints

Eight of nine high-bound ranges produced checked results in the
[scaled score calculation](ESA_ATTITUDE_SURVIVOR_SCORE_PLAN.md).
The combined upper bound changed from 54.01 to **54.00 standardized
units**, compared with a **25.41-unit** nominal forecast difference.
The remaining disc bound stayed at approximately 33.16 units.

One disc point moved the forecast **31.86 units** while meeting
the range's 270 inequalities, its box and the earlier GPS loss
constraint. A globe point passed the equivalent checks with a
movement of **18.15 units**. The points use shared coefficients
constrained by the inequalities. Whether one physical calibration
can produce all those coefficient values remains open.

Disc range 2/3 encountered a software error in the fallback for an
unsuccessful linear proposal. It completed two charges before the
run sealed as terminal. Its previous upper bound remains in the
cover. A regression test reproduced the error and verified the
corrected fallback. The failed task and its charges were preserved.

I replayed the same physical parameter values with all shared terms
derived from one calibration. Both points failed the earlier GPS
check. The earlier squared-loss increase went from 12.53 to 20,637.42
for globe and from 17.58 to 26,899.97 for disc. The relaxed points
passed because this comparison permits an earlier unshared error norm
of 0.1. [Physical replay](esa-attitude-survivor-physical-replay.json)

The verified disc point establishes that another search under the same
inequalities cannot reduce their support below the forecast difference.
The next step is to search with the shared terms linked from the start.
Aircraft prediction uncertainty and independent confirmation remain open.

[Sealed inputs, certificates and failed task](esa-attitude-survivor-score-evidence/README.md).

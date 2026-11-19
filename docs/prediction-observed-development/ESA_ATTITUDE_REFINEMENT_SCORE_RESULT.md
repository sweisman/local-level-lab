# Smaller attitude ranges leave the highest ESA bounds unchanged

The [refinement](ESA_ATTITUDE_REFINEMENT_SCORE_PLAN.md) covered the eight
highest-bound ranges with 32 smaller ranges. In every refined parent,
three children had a tighter upper bound on the possible movement,
while one still needed its parent's upper bound. The highest bound for
each candidate therefore stayed the same.

| Candidate | Original cover upper bound | Refined cover upper bound | Smaller ranges checked |
| --- | ---: | ---: | ---: |
| Zero-field globe | 26.734 | 26.734 | 16 |
| Zero-field disc | 34.241 | 34.241 | 16 |

The combined upper bound is still **60.97 standardized units**, compared
with a **25.41-unit** forecast difference. All eight tasks completed.
Twenty-seven numerical proposals reached their iteration limit.
The eight children that retained their parent's bound all reached
that limit. Every child remains in the cover.

Those eight cases need a different calculation. First check whether
they can fit the earlier GPS positions at all, using the same
calibration constraints and loss allowance. A checked certificate of
infeasibility could remove a range. An optimizer stopping status
cannot. No new trajectory fits or unused receiver positions were used.

The unchanged globe bounds are in parent/child ranges 4/2, 5/3, 6/2
and 7/2. The unchanged disc bounds are in child 1 of parents 0–3.
The complete refined covers have 12 globe ranges and 14 disc ranges
above half the nominal difference. A feasibility check can prioritize
the eight unchanged bounds and retain the certificates for any range
it cannot exclude.

[Sealed range boundaries, constraints and results](esa-attitude-refinement-score-evidence/README.md).

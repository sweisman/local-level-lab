# Smaller attitude ranges tighten the ESA calibration bound

Eight closed attitude ranges cover the full original calibration box
for each candidate. The combined upper bound on forecast movement
fell from **about 78.52 to 60.97 standardized units**. The nominal
globe–disc forecast difference is **25.41 units**.

| Candidate | Whole-box upper bound | Lowest range upper bound | Highest range upper bound |
| --- | ---: | ---: | ---: |
| Zero-field globe | 39.781 | 7.910 | 26.734 |
| Zero-field disc | 38.738 | 6.500 | 34.241 |

The comparison assumes an earlier unshared error norm of 0.1 per
candidate. The highest range bound counts for each candidate. The
two worst ranges fall in opposite halves of the vertical-axis attitude
range, so each candidate still needs its own complete cover.

All sixteen ranges were checked, with all 20 archived linked points
retained. Ten numerical proposals reached their iteration limit.
The bounds still follow from the checked certificates, using the
whole-box bound as a fallback. No new trajectory fits or unused
positions were involved. [Frozen plan](ESA_ATTITUDE_COVER_SCORE_PLAN.md)

The subdivision is effective, but its remaining bound still exceeds
the forecast difference. Refine the ranges that control each candidate's
upper bound while keeping the rest of the original range covered.
Four ranges per candidate exceed half the nominal forecast difference.
Each of the other eight ranges already has an upper bound below that
reference, so their existing certificates can remain in the cover.
The [follow-up](ESA_ATTITUDE_REFINEMENT_SCORE_RESULT.md) completed that
refinement. It retained the same maximum for both candidates.
The integrator's unshared error and independent aircraft accuracy
remain unqualified.

[Sealed range boundaries, constraints and results](esa-attitude-cover-score-evidence/README.md).

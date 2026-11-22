# Whole-path compatibility control

The [software control](JOINT_FUTURE_PROFILE_PLAN.md) now solves one bounded
linear calibration correction against an entire later path. Five known-answer
tests pass: an interior exact solution, a difference outside the nuisance
space, a rank-deficient boundary solution, permutation invariance, and
rejection of incomplete or nonfinite inputs. It retains all supplied
calibration columns and reports their singular-value rank and active bounds.

This matters because overlapping one-coordinate ranges do not prove that
one **shared** calibration setting can explain the whole path. Conversely,
a path difference inside the nuisance span remains indistinguishable by
this statistic. The calculation could be more informative than checking
whether every future coordinate falls inside every candidate's separate
range.

One sealed generated recording has now been scored with this helper; its
[saved nonlinear audit](GENERATED_JOINT_PROFILE_SAVED_RESULT.md) finds that
full-range calibration corrections move the native path metres to tens of
metres away from the linear tangent. Its linear costs cannot rank models.
It uses later observations to choose its bounded correction, so it is a
descriptive **compatibility profile**, not an earlier-only prediction test.
Its null distribution, nonlinear remainder, actual aircraft error law and
two-stage selection remain unqualified. It makes no model decision and does
not alter any frozen result. The next software gate is to supply a complete
training-conditioned **joint** whitening operator and candidate tangent
from a generated case, then check the profile against an independent
nonlinear calculation before any observed use.
The [joint whitening adapter](CONDITIONAL_JOINT_PROFILE_RESULT.md) has passed
its independent dense software control. A trusted local or fully nonlinear
profile and observed-aircraft qualification remain open.

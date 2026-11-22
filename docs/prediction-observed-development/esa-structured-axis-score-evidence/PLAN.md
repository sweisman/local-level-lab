# Score selected forecast axes without a dense covariance

Build a state-space operator for any selected later coordinates after
conditioning on all earlier observations. Run it on the same retained
forecast paths and covariance assumptions as the [height check](ESA_HEIGHT_ROLE_RESULT.md).
Verify every full and horizontal path score against the dense replay.
This advances the long-recording calculation while retaining the original
fit dispositions and scoring assumptions.

Before using the sealed inputs, check that the structured operator agrees
with an independently formed dense marginal conditional covariance for
correlated observations, a nonzero earlier conditioning period and
different axis selections. Check a saved checkpoint across later blocks.

Use the four completed ESA 187 covariance arms and their 20 paths each.
Reuse their exact earlier-conditioned errors and never access a protected
group. Run two generated size checks at 2,048 and 4,096 later epochs
under the same declared covariance model. Report the operator bytes and
the dense factor bytes at each size. These checks measure storage and
test finite scores. Keep timing as descriptive information.

Use six tasks, four original and two generated covariance constructions,
and at most 86 charged calculations. Use one thread, a 90-second
cooperative limit, and zero navigation calls. The generated matrices use
fixed receiver weights, the full drift operator and one-second stamps.
There is no GPS acquisition, fit, threshold selection or aircraft decision.

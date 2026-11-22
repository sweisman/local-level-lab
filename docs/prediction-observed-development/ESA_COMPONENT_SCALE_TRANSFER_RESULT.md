# Separate forecast-error scales have yet to transfer

On four matched turn and steady pairs from ESA development flight 187,
the original covariance and the fitted common multiplier each put
**one of eight held-out windows** inside the descriptive error reference.
The two descriptions of inertial measurement error gave the same counts.

The separate-scale optimizer met its stopping rule in **one of eight
checks**. Six stopped without meeting the rule, and one exhausted its
100-evaluation budget. All eight fitting designs had numerical rank
three. The one passing fit put steady-error variance at its lower bound,
with multipliers of 0.95 for native variance, 0.0067 for steady, and
20.50 for maneuver. Both of its held-out windows scored better on joint
log likelihood and remained outside the descriptive error reference.
There is no complete transfer comparison for that candidate.

The common multiplier improved the joint log score on three windows and
worsened it on five. Its total negative log score rose from −9,562 to
−9,413 for each inertial error description. On the worst-scoring turn,
the mean squared standardized error rose from 3.34 to 4.44, with one as
the Gaussian reference.

All eight technical tasks completed in 101 seconds on one thread. The
predicted paths, 120 later positions per window and original pairing
stayed fixed. Scale fitting omitted both windows in the scored pair.
All windows share one flight, and the Gaussian reference is descriptive.
Thirteen focused tests passed. The independent flights remain unopened.

The next numerical check can transform each error vector and component
into units of the native covariance before estimating the multipliers.
That improves conditioning while preserving the Gaussian objective up to
a fixed normalization. Any separate run must retain the original limits
and failures and verify its fitted scores against the dense calculation.
The [completed whitening comparison](ESA_WHITENED_SCALE_TRANSFER_RESULT.md)
verified the scores and left the stopping count at one of eight.

[Frozen method](ESA_COMPONENT_SCALE_TRANSFER_PLAN.md) ·
[Scores and optimizer outcomes](esa-component-scale-transfer-result.json) ·
[Execution receipts](esa-component-scale-transfer-evidence/README.md) ·
[Reproduction bundle](esa-component-scale-transfer-evidence/bundle.zip)

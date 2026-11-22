# Whitening leaves the forecast-error transfer unresolved

Changing coordinates preserved the Gaussian scores and left the optimizer
pass count at **one of eight**. The one pass switched from the point-rate
description to the increment description for the same pair of windows.
Both solutions place the steady variance at its lower bound and estimate
about 0.952 for the native variance and 20.50 for the maneuver variance.
The two held-out windows in the new passing fit both remain outside
the descriptive Gaussian error reference.

| Calculation | Fits that met numerical stopping | Held-out windows inside the reference with the passing fit |
| --- | ---: | ---: |
| Metre coordinates | 1/8 | 0/2 |
| Native-whitened coordinates | 1/8 | 0/2 |

The other seven whitened fits stopped without meeting the numerical rule.
Score checks at fixed and fitted scales reproduced the metre-coordinate
scores after restoring the known log determinant term. The common fitted
multiplier also reproduced. All eight technical tasks closed in 86 seconds
with one thread, and 13 focused tests passed. The original failures remain
recorded. This test reused one development flight, with no new trajectory
fits and no reserved flight access.

The optimizer outcomes leave a distinct question open. Can any admissible
set of scales put all eight windows within the error reference? A test of
the full scale range can address that question directly. Even a favorable
answer would describe these windows and would still require a separate
prediction test. The [completed range check](ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md)
found no compatible set in either inertial error description.

[Frozen method](ESA_WHITENED_SCALE_TRANSFER_PLAN.md) ·
[All scores and optimizer outcomes](esa-whitened-scale-transfer-result.json) ·
[Execution receipts](esa-whitened-scale-transfer-evidence/README.md) ·
[Reproduction bundle](esa-whitened-scale-transfer-evidence/bundle.zip)

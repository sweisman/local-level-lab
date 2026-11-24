# How the reserved flights differ from the development flight

The seven reserved training windows use the same report cadence as the
development flight. Their satellite geometry and motion differ. Every
reserved window has higher median PDOP at both training lengths. PDOP
describes the effect of satellite geometry on a position calculation.
The reported position precision remains a receiver estimate.

| Training length | Development median PDOP | Reserved median PDOP range | Reserved slices with higher 95th-percentile course rate |
| --- | ---: | ---: | ---: |
| 400 reports | 1.26 | 1.31–1.82 | 5 of 7 |
| 800 reports | 1.24 | 1.33–1.76 | 6 of 7 |

On the shorter split, six reserved median heights were outside the middle
90% of development heights. This count fell to zero on the longer split,
which includes more of the climb on the development flight. The longer
training period still left every reserved median PDOP above its development
range. These comparisons use one development window and give no accuracy
or eligibility threshold.

The result shows why a confirmation error model needs to cover different
satellite arrangements and stronger course changes. The original seven
slices and both training lengths are preserved. The check decoded only
earlier receiver values and verified the later clocks from the saved
layout. It read no later positions, inertial readings or model outcomes.
No model fits ran. Seven software tests passed. [Fixed plan](ESA_CONFIRMATION_TRAINING_PROFILE_PLAN.md) · [Exact input bindings](esa-confirmation-training-profile-freeze.json) · [Saved profiles](esa-confirmation-training-profile-result.json)

## Verify from the public files

The verifier ties the seven group identities to the timing and receiver
receipts. It checks that both earlier blocks end at the same report, followed
by the same 120 withheld reports. It also reproduces the comparisons above
from the saved profile summaries. This check needs only the public evidence.
The fixed plan has the steps for re-deriving the profiles from the earlier
receiver observations.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_evidence
```

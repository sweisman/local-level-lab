# The full ESA integration reproduces the linked forecast changes

The [archived scalar replay](ESA_LINKED_PHYSICAL_REPLAY_PLAN.md)
completed all four checks. The two points chosen under the original
earlier loss limit still pass it in the full integrating model.
Their combined movement toward the other forecast is **0.432 units**.
The nominal forecast difference is **25.41 units**.

| Candidate | Earlier unshared allowance used in the search | Full earlier loss increase | Full forecast movement | Earlier error left outside the linked map | Signed forecast error left outside the map |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zero-field globe | 0 | 0.009885 | 0.211178 | 0.0000160 | +0.0000069 |
| Zero-field disc | 0 | 0.009989 | 0.221021 | 0.0000328 | +0.0000255 |
| Zero-field globe | 0.1 | 13.115217 | 6.030138 | 0.0098598 | +0.0066313 |
| Zero-field disc | 0.1 | 19.456315 | 6.510155 | 0.0186694 | −0.0087748 |

The two points selected using the 0.1 allowance gave similar forecast
movements in the full calculation. Both exceeded the original
earlier loss increase limit of 0.01. The unshared error in the replay
was below 0.019 in the earlier norm and below 0.009 in the forecast
direction for all four points. Those observed errors apply to the
checked points. A bound over the entire allowed calibration range
remains open.

Both baseline replays matched the sealed paths within one nanometre.
The six charged passes covered two baselines and four point replays.
They used no later receiver positions, new fits or reserved recordings.

## What tightening the earlier error allowance changes

The same saved bounds still exceed the 25.41-unit forecast difference,
even if the earlier unshared error is assumed to be zero. This
sensitivity check reuses the original certificates and does no fitting.

| Assumed earlier unshared error norm | Combined upper bound |
| ---: | ---: |
| 0 | 53.66 |
| 0.02 | 53.73 |
| 0.05 | 53.83 |
| 0.1 | 54.00 |

The checked examples and the upper bounds leave a wide gap. Sharper
constraints linking the calibration terms are needed before this approach
can distinguish the two forecasts across the full calibration range.
The work remains a development check on one flight.

[Sealed replay inputs, source and results](esa-linked-physical-replay-evidence/replay.zip) ·
[Earlier-error sensitivity data](esa-earlier-allowance-sensitivity.json) ·
[Evidence for the calibration checks](ESA_CALIBRATION_EVIDENCE.md)

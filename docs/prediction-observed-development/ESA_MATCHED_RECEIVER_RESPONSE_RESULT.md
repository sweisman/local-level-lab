# Matching the derivative response removes the large first-window error

The position and velocity methods now agree much more closely on the
predicted force directions. The largest RMS difference between their
angle sets fell from **1.017° to 0.030°**. On the first straight-course
window, the worst position-derived globe error fell from **1.019°
to 0.046°** when the specified field was retained and the antenna
offset was applied. That comparison covers all three receiver
products and both averaging widths.
[Earlier derivative comparison](ESA_DIRECTION_RECEIVER_DERIVATIVE_RESULT.md)

| Direction comparison | Original derivative methods | Matched derivative methods |
| --- | ---: | ---: |
| Median RMS change when switching from velocities to positions | 0.0209° | 0.0042° |
| Largest RMS change when switching from velocities to positions | 1.017° | 0.030° |
| Comparisons with lower globe error | 576 of 576 | 576 of 576 |
| Zero-field comparisons with lower globe error | 192 of 192 | 192 of 192 |

The new quadratic fit responds identically to positions and velocities
that agree under trapezoidal integration. That makes the large old
difference a property of the earlier differentiation methods on this
recording. For the matched method, remaining position–velocity
differences can include receiver error or motion between samples.

Force magnitude still gives much weaker separation. The median
globe–disc magnitude difference is **0.027 mm/s²**. The median
later error against the separate GIRAFE measurement is **1.24 mm/s²**
from position derivatives and **1.30 mm/s²** from reported velocities.
The direction ranking is robust to the tested receiver choices.
Both kinds of score still come from one development flight.
Absolute prediction limits and independent-flight uncertainty remain open.

The batched direction calculation agrees with the original scalar
calculation in the software checks. In a one-thread timing check on 32
identical generated evaluations, it took 0.15 seconds versus 0.74
seconds for scalar evaluation. All eight flight-window tasks passed
their frozen limits. [Frozen design](ESA_MATCHED_RECEIVER_RESPONSE_PLAN.md) ·
[Saved force, direction and work records](esa-matched-receiver-response-result.json)

To verify the saved report, restore
`data/esa-matched-receiver-response-v1` and run the following command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_matched_receiver_response report
```

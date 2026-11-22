# The two instruments agree much more closely on the ground

The campaign measured gravity on the aircraft parking aprons. The
two preselected ground stops in our recording were about **3 m**
from the Nuuk reference and **47 m** from the Reykjavík reference.
These measurements give an external check on the scale of both
instruments while parked. [Campaign paper, Table 2](https://essd.copernicus.org/articles/17/1667/2025/#section3.3)

| Airport and GIRAFE export | iMAR minus measured gravity | GIRAFE minus measured gravity | GIRAFE minus iMAR using mean sample magnitude |
| --- | ---: | ---: | ---: |
| Nuuk, Nuuk–Reykjavík | +0.282 mm/s² | −0.003 mm/s² | −2.270 mm/s² |
| Reykjavík, Nuuk–Reykjavík | +0.444 mm/s² | −0.008 mm/s² | −2.053 mm/s² |
| Reykjavík, Reykjavík–Akureyri | +0.444 mm/s² | +0.010 mm/s² | −2.014 mm/s² |

The two reference columns use the magnitude of the mean force vector
and account for the small height difference between the sensor and
the apron point. That correction moves each result by less than
0.006 mm/s². The GIRAFE exports cover different portions of the
Reykjavík stop and overlap in time. Their two rows reuse the same
saved iMAR stop average. Minute-mean GIRAFE force varied by up to
0.412 mm/s², and the precise match of longer averages leaves local
gravity gradients and the remaining aircraft motion unresolved.

The final column uses the mean of the sample magnitudes, as in the
airborne comparison. The ground difference on that scale is about
2.0–2.3 mm/s². In flight it is **26–29 mm/s²**. The change between
conditions calls for checking airborne motion, averaging and instrument
processing before assigning the disagreement to either sensor.
[Airborne force comparison](ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)

Both ground tasks passed. They used all GIRAFE rows inside the
preselected stops and reused the saved iMAR vector means. The
same-statistic comparison in the last column uses the sample
magnitudes from two prior iMAR reports after verifying their full
iMAR stop times against the two tie records. No Earth model was fitted.
[Frozen design](ESA_GIRAFE_GROUND_TIES_PLAN.md) ·
[Saved apron comparisons](esa-girafe-ground-ties-result.json) ·
[Nuuk iMAR sample magnitudes](ground-imu-rate-result.json) ·
[Reykjavík iMAR sample magnitudes](second-ground-imu-result.json)

To verify the saved apron comparison, restore
`data/esa-girafe-ground-ties-v1` and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_ground_ties report
```

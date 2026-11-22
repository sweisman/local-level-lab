# Eight receiver paths preserve the matched-field shape preference

The zero-field globe had the lower squared forecast error on all eight
receiver paths from ESA development flight 187. This held after allowing
smooth position, velocity and acceleration corrections. The receiver
choice still mattered. The GPS L1-only solution brought the score
from **−6.92 to −1.07**, close to the point where the two models tie.

| Receiver path | Signed shape score | Globe RMS in the working error units |
| --- | ---: | ---: |
| Original receiver export | −6.92 | 1.20 |
| GPS L1 code only | −1.07 | 11.15 |
| GPS dual-frequency code | −11.55 | 33.44 |
| GPS with final satellite orbits | −10.89 | 33.43 |
| GPS broadcast without G17 | −10.65 | 34.47 |
| GPS clock changes without G17 | −9.83 | 34.46 |
| GLONASS L1 code only | −12.65 | 24.81 |
| GLONASS dual-frequency code | −3.51 | 77.95 |

Zero is a tie. Negative scores favor the globe in this comparison, with
the same zero background field for both models. The incremental effect
of the orbit replacement was +0.66 score units. The clock change shifted
the score +0.82 on the same reduced satellite set. Across all eight
paths, altered positions in the earlier part contributed at most 0.28
units to the score change through conditioning. Altered later positions
contributed up to 5.81 units.

The RMS column divides the squared errors by the same 360 later coordinate
entries before taking square roots. These are residuals after the smooth
adjustment, expressed in the working covariance units. The much larger
code-only errors show that comparing rankings across receiver products
provides little justification for applying the same uncertainty model to
all products. The score reuses fixed fitted calibrations on one flight.
All eight solutions share the aircraft antenna. This checks sensitivity
to receiver processing, while absolute prediction adequacy and
flight-to-flight uncertainty remain open.

The 25.41-unit separation of the forecast paths measures how far apart
the two fixed predictions are. The 1.07-unit GPS L1 margin measures how
far the observed score is from a tie. A robustness claim about that
observed ranking needs bounds on changes to the midpoint score, including
receiver error and remaining fitted-calibration freedom.

The replay recovered the archived **25.41-unit** separation between the
predictive paths after the smooth adjustment. The direct squared-error
comparison and the signed score gave the same result on every receiver
path. No fit or forecast propagation ran, and the reserved ESA flights
remained sealed.

## Reproduce the score

Use the sealed original forecast pair and receiver products from the
earlier development studies. The freeze records their hashes. Run from
the repository root with the frozen numerical environment.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_receiver_replay freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_receiver_replay calculate
```

[Fixed method](ESA_SHAPE_RECEIVER_REPLAY_PLAN.md) ·
[Source and input freeze](esa-shape-receiver-replay-freeze.json) ·
[Scores and separate earlier and later effects](esa-shape-receiver-replay-result.json)

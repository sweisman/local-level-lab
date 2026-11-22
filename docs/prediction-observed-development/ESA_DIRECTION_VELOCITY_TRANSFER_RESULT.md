# The small disc preference follows the training velocity source

With 11-report averaging and the specified background field retained,
fits trained on GLONASS velocity favored the disc with **all three**
later velocity sources. Fits trained on either the receiver export or
GPS Doppler favored the globe with all three. The comparison therefore
traces the earlier reversal to the calibration and alignment selected
using GLONASS in training.

| Velocity used in training | Later receiver export | Later GPS Doppler | Later GLONASS Doppler |
| --- | ---: | ---: | ---: |
| Receiver export | +0.00523° | +0.00457° | +0.00138° |
| GPS Doppler | +0.00603° | +0.00535° | +0.00205° |
| GLONASS Doppler | −0.00520° | −0.00554° | −0.00690° |

The table shows disc minus globe angular RMS. Positive entries favor
the globe. Each row keeps the earlier calibration and starting alignment
fixed. All 36 original later scores reproduced when training and scoring
used the same source.

| Matched field and averaging | Largest score-gap change from training source | Largest change from scoring source |
| --- | ---: | ---: |
| Zero field, 11 reports | 0.00297° | 0.00022° |
| Field retained, 11 reports | 0.01123° | 0.00398° |
| Field removed from gyro, 11 reports | 0.00219° | 0.00020° |
| Zero field, 25 reports | 0.00103° | 0.00018° |
| Field retained, 25 reports | 0.03706° | 0.00238° |
| Field removed from gyro, 25 reports | 0.00008° | 0.00017° |

The globe had lower angular error in 51 of 54 cells. These cells reuse
the same flight and are sensitivity checks. The three velocity products
share the receiver position reference and aircraft antenna. Their spread
cannot establish absolute direction error or rule out a common error. The
test fixes both the calibration and alignment when changing the scoring
source. It does not identify which receiver velocity was more accurate.

All 36 replays completed, with no new calibration search, original data-file
read or reserved-flight read. The original 120 position holdouts stayed
outside the comparison.

## Reproduce the results

With the closed `data/esa-direction-velocity-transfer-v1` study restored,
verify and rebuild the scores from its sealed records without reintegrating
the gyro packets.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_velocity_transfer report
```

[Frozen design](ESA_DIRECTION_VELOCITY_TRANSFER_PLAN.md) ·
[All source swaps, angles and charges](esa-direction-velocity-transfer-result.json)

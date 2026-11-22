# Paired recorder alignment on unseen seconds

A fixed relative rotation and rate offset were estimated from the earlier half of each published same-track pair, then applied unchanged to the later half. The comparison uses recorded gyro bins only.

12/12 pairs passed the fixed numerical rank check for a rotation; noise can also create apparent rank. Median later-half vector RMS was 12.72°/h with an earlier-only offset and 12.26°/h with an earlier-only offset plus rotation among identifiable pairs. For fixed complete 10-second windows, the medians are 1.74 and 1.63°/h; for one-minute windows, 0.38 and 0.31°/h. Adjacent windows and pairs are dependent. This is a relative recorder check, not an intrinsic sensor-noise measurement.

| Shared leg | Priority | Rotation identified | Offset-only RMS (°/h) | Rotation + offset RMS (°/h) |
| --- | --- | --- | ---: | ---: |
| leg-13805a9a35c4 | no | yes | 16.06 | 14.44 |
| leg-590ee7971efb | yes | yes | 20.78 | 15.89 |
| leg-9c109162b404 | yes | yes | 8.26 | 8.18 |
| leg-63c877c00c40 | no | yes | 28.69 | 28.71 |
| leg-57f1dae19c0f | no | yes | 4.53 | 4.25 |
| leg-bf6c72fb73b4 | yes | yes | 20.37 | 20.32 |
| leg-a37ab8671511 | no | yes | 11.70 | 11.62 |
| leg-1c0a0583b775 | no | yes | 35.26 | 35.20 |
| leg-8e6717c0a5a0 | no | yes | 4.60 | 4.47 |
| leg-47a9a0ba5806 | no | yes | 7.75 | 7.65 |
| leg-b8eb186f98a8 | no | yes | 5.26 | 5.20 |
| leg-530cceb77358 | no | yes | 13.74 | 12.90 |

The rotated fit improves later-half RMS in 11 of 12 pairs, but the remaining differences are substantial. The comparison cannot distinguish sensor calibration from mounting, timing, processing or real aircraft motion. The pairs share flight conditions and are not independent confirmations. No Earth-model decision or ESA error law follows.

[Fixed method](PLAN.md) · [All fitted and held-out values](RESULT.json).

# Parallel GNSS receivers on the opened ESA flight

Two additional PPP exports from recording 187 were downloaded with verified sizes, hashes and resumable receipts. The source campaign reports three physical GNSS receivers sharing one aircraft antenna. This check compares only the 400 earlier `air1` training times; no withheld report or protected flight was analyzed.

| Other export | Matched earlier epochs | Largest time offset (s) | Maximum motion during time offset (m) | North/east/up position RMS difference (m) | North/east/up velocity RMS difference (m/s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| mosaic03 | 400 | 0.0006 | 0.045 | 0.011/0.022/0.027 | 0.012/0.008/0.019 |
| pwrpak7 | 400 | 0.0005 | 0.037 | 0.008/0.021/0.035 | 0.012/0.007/0.019 |

Matches require timestamps within 2 ms and use no interpolation. The motion column bounds the apparent displacement from each time offset using reported speed; it has not been subtracted. The detailed result also gives signed means and variation after subtracting a constant offset. The separate receiver hardware gives a real cross-check, but the antenna is shared and PPP processing may have common errors. Pairwise disagreement can expose error; agreement does not prove absolute accuracy or calibrate the IMU error law. No Earth-model decision follows.

[Fixed method](PARALLEL_GNSS_PLAN.md) · [Detailed result](PARALLEL_GNSS_RESULT.json) · [Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/essd-17-1667-2025.html).

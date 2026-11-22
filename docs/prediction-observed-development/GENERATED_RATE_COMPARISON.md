# Short-timescale IMU changes in recorded and generated data

The known-answer generated fits leave much larger training errors than the
ESA development fit. This saved-only comparison checks whether their IMU
inputs have similar short-timescale behavior. It uses the first **600 seconds**
of each generated recording and the existing **800-second** ESA training-rate
study. Both sample at about 300 Hz. Their durations differ, so this is a
descriptive comparison, not a matched noise estimate.

For each axis, the calculation takes three equally spaced rate samples and
removes their straight-line trend. The table gives the RMS of that contrast.
The shortest span is about 0.0067 seconds; the longer span is about 2 seconds.

| Recording | Span | Gyro Y, rad/s | Force Z, m/s² |
|---|---:|---:|---:|
| ESA development | 0.0067 s | **0.02396** | **2.388** |
| Generated, increment-error truth | 0.0067 s | 0.000101 | 0.00346 |
| Generated, point-error truth | 0.0067 s | 0.0000413 | 0.00141 |
| ESA development | 2 s | 0.02317 | 2.254 |
| Generated, increment-error truth | 2 s | 0.00278 | 0.0268 |
| Generated, point-error truth | 2 s | 0.00279 | 0.0264 |

The full [saved report](GENERATED_RATE_COMPARISON.json) gives all six axes at
four spans. The recorded short-span variation is much larger than either
generated stream, despite the recorded fit's much smaller whitened training
error. At two seconds the comparison varies by axis: for example, the
generated X-gyro contrast is larger than the recorded one. A single
scale factor cannot make the two rate-variation patterns match.

These body-axis changes include aircraft maneuvering, vibration and any
onboard processing. They do **not** isolate IMU sensor noise or explain the
later height-prediction failure. The ESA rate study is read from its sealed
historical artifact; its source is not replaced with today's library code.
No original recording, later receiver value or reserved confirmation flight
was opened, and no fit was repeated. The scientific decision remains
**abstain**.

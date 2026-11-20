# What motion do the saved force directions require?

The rate ranges for all four candidates overlapped on both recordings for
every matched clock, receiver path and time split. The check used **991 saved
windows** and no gyroscope measurements. It examined one accelerometer packet
per window, with half-count uncertainty and zero calibration correction.

| Recorder | Period | Sampled directions | Necessary rate, across cases | Rate of a verified nominal path, across cases |
|---|---|---:|---:|---:|
| IMU8 | Earlier | 415 | 3.93–3.94°/s | 4.07–4.09°/s |
| IMU8 | Later | 193 | 3.81–3.85°/s | 3.95–3.99°/s |
| IMU21 | Earlier | 265 | 3.13–3.19°/s | 3.19–3.21°/s |
| IMU21 | Later | 118 | 3.145–3.165°/s | 3.167–3.169°/s |

The largest change in a necessary rate across candidates was 0.056°/s with the
other settings held fixed. Changing receiver paths moved it by up to
0.0014°/s, and changing the clock moved it by up to 0.0006°/s. Testing all 64
rate brackets at their midpoints found 40 verified paths and left 24 probes
inconclusive. None of the probes tightened a lower bound by exclusion.

These rates describe sampled orientation paths that align the force directions
under the stated assumptions. The calculation treats each packet's average
direction as its midpoint direction and each fitted receiver path as supplied.
It has no independent aircraft rate limit. The ranges do not establish actual
aircraft motion, physical adequacy or whether acceleration alone can distinguish
the models under a complete uncertainty budget.

The replay uses 15,856 required-force evaluations and zero navigation fits
or raw-file decodes. Run it from the repository root using the frozen
environment and saved inputs.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_recorded_motion_rate replay
```

[Fixed method](RECORDED_MOTION_RATE_PLAN.md) · [Input hashes and budget](recorded-motion-rate-freeze.json) ·
[All 64 rate brackets](recorded-motion-rate-receipt.json)

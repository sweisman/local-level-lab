# The same aircraft forecast scored against two receivers

On one IMU8 survey leg, the specified-field globe forecast stayed closest
to the later positions from both GPS receivers. The ranking held over the
first 30, 60 and 120 seconds and across the full 223-second forecast, for
both horizontal position and height. The zero-field disc fit did not pass
its stopping check, so the full four-model comparison remains incomplete.

| GPS reference | Globe, specified field | Disc, same field | Globe, zero field |
|---|---:|---:|---:|
| Onboard receiver | 19.36 m | 242.51 m | 1,363.43 m |
| Second receiver | 31.17 m | 257.93 m | 1,380.04 m |
| Second receiver with earlier offset removed | 19.86 m | 242.63 m | 1,363.40 m |

The table gives full-forecast horizontal RMS error. The corresponding height
errors across the three references were 9.92–10.49 m for the specified-field
globe, 21.68–22.22 m for the same-field disc, and 23.83–24.39 m for the
zero-field globe.

The second receiver covered all 445 earlier and 223 later GPS epochs at
exactly matching epoch tags. Its earlier median position offset was 11.22 m
north, 16.97 m west and 0.14 m up. With that offset held fixed, the two
receivers differed later by 0.59 m north, 0.26 m east and 0.45 m vertically
in RMS. The forecast paths were already sealed. The replay used no new fit,
receiver position solve or interpolation and reproduced the receipt byte for
byte.

This is a retrospective check on one flight. The receivers can share
satellite and processing errors, and their offset may include antenna
separation. The result shows stability to this receiver change. Absolute
forecast accuracy and independent-flight replication still need validation.

From the repository root, replay with the frozen Python environment and
the archived forecast and receiver inputs.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_companion_forecast replay
```

[Method](COMPANION_FORECAST_PLAN.md) · [Fixed inputs and budget](companion-forecast-freeze.json) ·
[Results and hashes](companion-forecast-receipt.json)

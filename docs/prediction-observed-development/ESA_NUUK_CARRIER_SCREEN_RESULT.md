# Why the nearby Nuuk comparison lost 20 seconds

The permanent Nuuk recording had continuous observations through the
full comparison. All **20 excluded seconds** fell below the five-satellite
minimum at the Doppler check, before computing the satellite ranges.
On those seconds, 194 satellite observations failed that check, one
lacked the required continuity or signal, and 13 passed.

| One-second intervals | Median size of the shared L1 phase–Doppler difference | Median RMS around the shared difference |
| --- | ---: | ---: |
| 20 excluded | 0.498 cycles | 0.0395 cycles |
| 100 retained | 0.144 cycles | 0.0396 cycles |

The shared difference is the median across satellites within each second.
It exceeded the 0.35-cycle threshold in absolute value in every excluded
second, with both positive and negative signs. The spread among satellites
around that value was similar in retained and excluded seconds. The
pattern points to a common receiver effect. Its origin is unresolved.

The replay verified the original carrier acceptance before applying the
range model. The saved 100-interval comparison and its thresholds stay
fixed. A separate clock-aware screen would need to distinguish a common
shift from satellite-specific tracking errors before changing which data
enter another comparison. All 121 planned checks completed. There were
zero new fits and no reads of reserved flights.
[Fixed plan](ESA_NUUK_CARRIER_SCREEN_PLAN.md) ·
[Results by second](esa-nuuk-carrier-screen-result.json) ·
[Original nearby-station comparison](ESA_NUUK_NEAR_STATIONS_RESULT.md)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_nuuk_carrier_screen report
```

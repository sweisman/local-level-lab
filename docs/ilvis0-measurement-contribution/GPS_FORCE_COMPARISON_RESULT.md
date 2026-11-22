# GPS processing changes the force estimates more than their shape difference

Onboard GPS, L1 code and dual-frequency code gave the **same sign of the
globe-minus-disc force difference in all 3,213 supported windows**, with
both shapes using the same background field. The comparison kept both
the zero-field and specified-field cases. It used the same epochs and
polynomial for every GPS stream. Another 123 windows lacked complete
support near the ends and were retained as abstentions.

The table gives the largest 95th-percentile change across the two
recordings and the two reconstructed GPS streams. Values are in m/s².

| Window duration | Force magnitude for an individual model | Globe–disc magnitude difference with matching fields | Globe–disc magnitude difference when only GPS height is exchanged |
|---|---:|---:|---:|
| 10 seconds | 0.190 | 0.0149 | 0.0000480 |
| 20 seconds | 0.0418 | 0.00155 | 0.00000835 |
| 30 seconds | 0.0181 | 0.000689 | 0.00000361 |

Exchanging height alone reproduced most of the force change for an
individual model and much less of the change in the shape difference.
The receiver-processing differences in latitude and longitude therefore
matter when the two shapes are compared. Longer windows reduced the
changes and also smooth real aircraft motion.

The sign describes which shape requires the larger force given a GPS
path. An accelerometer measurement is needed to say which prediction
fits. All results here use GPS positions alone. The methods share
satellite inputs and can miss errors common to their trajectories.

The [fixed calculation](GPS_FORCE_COMPARISON_PLAN.md), [configuration
freeze](gps-force-comparison-freeze.json), [window table](gps-force-comparison-windows.csv.gz)
and [verified receipt](gps-force-comparison-receipt.json) preserve the
64,260 analytic force calculations and their inputs. There were zero
position solves and inertial fits.

The [next inertial input check](MATCHED_OBSERVED_PREFLIGHT_PLAN.md) uses
the same two recordings. The saved layout identifies 1,111 exact common
receiver epochs and fixes the training and later scoring cuts.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_gps_force_comparison replay
```

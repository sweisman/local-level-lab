# Receiver-only forecast baseline

A constant-velocity line fitted to the **last 60 seconds of earlier GPS receiver positions**
was extrapolated across the same withheld periods as the three-recording IMU pilot.
The forecast used no IMU values and saw no withheld positions before it was saved.
All three saved tasks completed with zero native model calls.

| Recording | Withheld time | North RMS | East RMS | Height RMS | Horizontal RMS |
|---|---:|---:|---:|---:|---:|
| `0e73879f…` | 3.7 min | 42.02 m | 75.67 m | 9.13 m | 86.55 m |
| `3df34ea3…` | 3.7 min | 144.23 m | 320.49 m | 7.09 m | 351.45 m |
| `7024120d…` | 2.4 min | 191.88 m | 53.55 m | 19.24 m | 199.21 m |

This is a descriptive prediction baseline, **not an Earth-shape test**.
It uses receiver coordinates and assumes constant local velocity for a minute.
A difference from an IMU forecast does not identify which IMU channel caused it.
The three recordings were already used for development; these results do not
calibrate confidence or prove independent replication.

[All scores](results.csv) · [Frozen method](PLAN.md) ·
[Original IMU pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)

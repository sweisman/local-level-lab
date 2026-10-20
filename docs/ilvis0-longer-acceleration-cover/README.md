# Longer complete prediction comparison

48/48 sectors pass; state: complete.

These are complete generated prediction ranges at 7.2 seconds, using six earlier observations. They are not aircraft errors, recording-scale confidence intervals or scientific detections.

| Model | Processing case | Complete | Width N / E / height (m) |
|---|---|---|---:|
| Globe with specified field | Zero removal | Yes | 2.582, 2.898, 1.891 |
| Globe with specified field | Profiled removal | Yes | 2.667, 2.973, 1.977 |
| Globe with zero field | Zero removal | Yes | 2.308, 2.377, 1.650 |
| Globe with zero field | Profiled removal | Yes | 2.465, 2.537, 1.807 |
| Flat disc | Zero removal | Yes | 2.031, 0.620, 1.538 |
| Flat disc | Profiled removal | Yes | 2.215, 0.675, 1.721 |

The study used 144 native evaluations and 384 bounds in 2779.8 seconds. All original physical bounds, orientation sectors and 42 columns remain. Longer horizons, numerical error and observational uncertainty still need qualification.

[Frozen scope](PLAN.md) · [Short comparison](../ilvis0-acceleration-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

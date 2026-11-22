# Do small stopping corrections change later forecasts?

**In these three selected cases, very little.** The test compared each saved
forecast with one new forecast from its saved bounded correction. It did not
use receiver positions from the later interval to form either new forecast
or choose a correction.

| Saved numerical case | Later north RMS change | East RMS change | Up RMS change | Largest horizontal change |
|---|---:|---:|---:|---:|
| Smallest failed cost change | 0.014 mm | 0.011 mm | 0.0007 mm | 0.038 mm |
| Middle failed cost change | 0.018 mm | 0.011 mm | 0.0057 mm | 0.052 mm |
| Largest failed cost change | 3.93 mm | 7.51 mm | 0.414 mm | 16.3 mm |

The separately frozen [v2 repair plan](CORRECTION_FORECAST_REPAIR_PLAN.md)
fixed a missing native C source in the first attempted study. That first
study sealed three technical failures **before any native call**; none were
reclassified or rerun within it. The repaired study
`ilvis0-correction-forecast-development-v2-20261118` completed 3/3 tasks,
charged exactly three native calls and 110,495,945 packet visits, and has
manifest SHA-256
`89216b4e43197491e93a3e5af0456f52b74b8a8abfc6f56811802ea8ae266837`.
All nine source-bound software checks passed.

These are **differences between predicted paths**, not errors against the
actual later receiver track. The cases were chosen by the smallest, middle
and largest *failed numerical cost change* among 49 saved probes. They are
useful for diagnosing the stopping check, but cannot estimate a population
failure rate, establish forecast accuracy or make an Earth-model decision.
The original 50 nonpassing fit labels remain unchanged. Independent
known-answer controls and a separately frozen observed method are still
needed before revising that stopping rule.

# Full-history prediction feasibility

0/6 numerical checks complete; 0/6 useful predictions. Elapsed 19.10 seconds.

| Candidate | Processing | Outcome | Total widths N / E / height |
|---|---|---|---:|
| Specified-field globe | Zero removal | Failed: native query failed or reported unsupported motion | Unavailable |
| Specified-field globe | Profiled removal | Failed: native query failed or reported unsupported motion | Unavailable |
| Zero-field globe | Zero removal | Failed: native query failed or reported unsupported motion | Unavailable |
| Zero-field globe | Profiled removal | Failed: native query failed or reported unsupported motion | Unavailable |
| Flat disc | Zero removal | Failed: native query failed or reported unsupported motion | Unavailable |
| Flat disc | Profiled removal | Failed: native query failed or reported unsupported motion | Unavailable |

Charged 6/72 native queries, 0/36 bounds and 0/31,104,000 logical bound steps.

The full eight-minute generated inputs and broad 27-parameter domains are retained, including ±1 second of clock uncertainty. Five training epochs ending at 290 seconds constrain a prediction at 438 seconds. Both stages retain every earlier inequality. The declared training error is ±1 metre per coordinate.

The fixed usefulness target is total width ≤20 m north/east and ≤50 m vertically in every case. It is a development target, not a scientific detection threshold or aircraft accuracy specification. Future truth is generated only after the prediction is saved.

These controls use no aircraft observations, protected ESA outcomes or optimizer starts. Even a complete pass does not establish all later epochs, an observational error law or whole-program floating-point coverage. Earlier failures remain preserved; no observed prediction fits follow automatically.

[Frozen calculation and limits](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

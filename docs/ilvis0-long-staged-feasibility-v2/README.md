# Full-history prediction feasibility

6/6 numerical checks complete; 0/6 useful predictions. Elapsed 29257.25 seconds.

| Candidate | Processing | Outcome | Total widths N / E / height |
|---|---|---|---:|
| Specified-field globe | Zero removal | Too wide | 2.0266e+06 / 2.4133e+06 / 1.4627e+06 m |
| Specified-field globe | Profiled removal | Too wide | 2.0245e+06 / 2.4187e+06 / 1.461e+06 m |
| Zero-field globe | Zero removal | Too wide | 1.7041e+06 / 1.9956e+06 / 1.2588e+06 m |
| Zero-field globe | Profiled removal | Too wide | 1.6998e+06 / 2.0019e+06 / 1.253e+06 m |
| Flat disc | Zero removal | Too wide | 6.5726e+05 / 1.0931e+05 / 3.1276e+05 m |
| Flat disc | Profiled removal | Too wide | 6.8752e+05 / 1.1491e+05 / 3.3927e+05 m |

Charged 72/72 native queries, 36/36 bounds and 31104000/31,104,000 logical bound steps.

The full eight-minute generated inputs and broad 27-parameter domains are retained, including ±1 second of clock uncertainty. Five training epochs ending at 290 seconds constrain a prediction at 438 seconds. Both stages retain every earlier inequality. The declared training error is ±1 metre per coordinate.

The fixed usefulness target is total width ≤20 m north/east and ≤50 m vertically in every case. It is a development target, not a scientific detection threshold or aircraft accuracy specification. Future truth is generated only after the prediction is saved.

These controls use no aircraft observations, protected ESA outcomes or optimizer starts. Even a complete pass does not establish all later epochs, an observational error law or whole-program floating-point coverage. Earlier failures remain preserved; no observed prediction fits follow automatically.

[Frozen calculation and limits](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

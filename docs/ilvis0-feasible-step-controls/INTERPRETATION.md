# What the accepted alternatives show

These are generated-data sensitivity checks, not measured aircraft position errors.

**6/6 cases** contain accepted saved alternatives whose later predictions differ by more than at least one original width target. The limits are 20 m north, 20 m east and 50 m height.

| Model | Processing case | Feasible saved points | North spread (m) | East spread (m) | Height spread (m) |
|---|---|---:|---:|---:|---:|
| Globe + field | Zero removal | 7 | 23.042 | 5.616 | 6.572 |
| Globe + field | Profiled removal | 7 | 23.034 | 4.466 | 6.545 |
| Globe, zero field | Zero removal | 7 | 22.988 | 6.083 | 6.616 |
| Globe, zero field | Profiled removal | 7 | 23.008 | 4.863 | 6.573 |
| Stationary disc | Zero removal | 7 | 23.136 | 6.154 | 6.660 |
| Stationary disc | Profiled removal | 7 | 23.270 | 6.356 | 6.539 |

Each number is a **lower spread among sampled feasible calibrations**, with the declared numerical guard subtracted. It is not an upper uncertainty bound. Different axes may use different pairs; the exact records and pair identities are preserved in the evidence.

All alternatives use the same earlier observations, physical bounds and input measurements. If two allowed calibrations exceed a width target, a more efficient enclosure or optimizer cannot make a valid range containing both narrower than that separation. Whether the declared calibration and error assumptions adequately describe aircraft recordings is a separate question.

The numerical guard has not been independently qualified for the entire recording. These results describe the saved native calculation under that assumption; they do not establish statistical confidence or qualify V01. The 53-stretch model preferences are unchanged.

[First-step outcomes](README.md) · [Fixed method](PLAN.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)

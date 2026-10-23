# Do more frequent earlier positions exclude the accepted alternatives?

This generated-data diagnostic reevaluates 18 existing calibrations without fitting them. It adds prediction times at one-second spacing from 2 to 290 seconds. No receiver observations are invented.

**18/18 fixed predictions completed.** All passing records preserve the original sparse epoch values exactly.

| Model | Processing case | Shared observation possible at every sampled training epoch? | Minimum north overlap (m) | Minimum east overlap (m) | Minimum height overlap (m) |
|---|---|---|---:|---:|---:|
| Globe + field | Zero removal | No | 0.0488 | -0.1801 | 0.0743 |
| Globe + field | Profiled removal | No | 0.0514 | -0.2449 | 0.0743 |
| Globe, zero field | Zero removal | No | 0.0521 | -0.1831 | 0.0742 |
| Globe, zero field | Profiled removal | No | 0.0547 | -0.2156 | 0.0743 |
| Stationary disc | Zero removal | Yes | 0.0546 | 0.0735 | 0.0741 |
| Stationary disc | Profiled removal | Yes | 0.0579 | 0.0737 | 0.0742 |

The original calibration and both accepted north-extreme alternatives each receive a ±1 m coordinate interval, expanded by the declared 0.00001 m numerical guard. A negative overlap means no common coordinate could satisfy all three at that epoch, even with that extra guard. Nonnegative overlap leaves their coexistence possible; it does not predict the noise an actual receiver would produce.

This tests only these fixed alternatives at sampled times. It is not a new outer prediction bound, a continuous-time guarantee, an aircraft error law or an Earth-model comparison. **V01 remains unqualified.** The 53-stretch findings are unchanged.

[Frozen method and limits](PLAN.md) · [Accepted alternatives](../ilvis0-feasible-step-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)

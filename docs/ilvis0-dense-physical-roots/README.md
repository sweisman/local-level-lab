# Starting prediction bounds without old training assumptions

Six fixed generated histories test the first training query with the full physical calibration range and no older one-metre training constraints. No aircraft original or future receiver observation is used.

| Candidate | Processing | Starting calculation |
|---|---|---|
| Globe + field | Zero removal | Supported |
| Globe + field | Profiled removal | Supported |
| Globe, zero field | Zero removal | Supported |
| Globe, zero field | Profiled removal | Supported |
| Stationary disc | Zero removal | Supported |
| Stationary disc | Profiled removal | Supported |

**6/6 starting calculations passed.**

This tests support at two seconds, not complete-cadence prediction or empirical noise coverage. An unsupported calculation is a software limitation and does not reject an Earth candidate. Earlier aircraft findings and all frozen failures remain unchanged.

[Frozen limits](PLAN.md) · [Complete-cadence requirements](../ilvis0-joint-projection-controls/NEXT_PLAN.md)

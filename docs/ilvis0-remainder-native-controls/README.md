# Conditional remainder in numerical integration

12/12 controls pass; 12/12 completed. Elapsed 919.93 seconds.

| Model | Processing | Force domain | Outcome | Force remainder, old → new (m/s²) |
|---|---|---|---|---:|
| Specified-field globe | Zero removal | physical | Pass | 53.156 → 28.678 |
| Specified-field globe | Zero removal | conditioned | Pass | 53.156 → 4.7817 |
| Specified-field globe | Profiled removal | physical | Pass | 53.156 → 28.678 |
| Specified-field globe | Profiled removal | conditioned | Pass | 53.156 → 4.7817 |
| Zero-field globe | Zero removal | physical | Pass | 53.156 → 28.678 |
| Zero-field globe | Zero removal | conditioned | Pass | 53.156 → 4.7817 |
| Zero-field globe | Profiled removal | physical | Pass | 53.156 → 28.678 |
| Zero-field globe | Profiled removal | conditioned | Pass | 53.156 → 4.7817 |
| Flat disc | Zero removal | physical | Pass | 53.156 → 28.678 |
| Flat disc | Zero removal | conditioned | Pass | 53.156 → 4.7817 |
| Flat disc | Profiled removal | physical | Pass | 53.156 → 28.678 |
| Flat disc | Profiled removal | conditioned | Pass | 53.156 → 4.7817 |

Charged 48/48 native queries and 24/24 bounds.

These four-second generated controls preserve all 27 physical directions, 24 shared error columns, the broad calibration region and ±1-second clock. Passing requires unchanged coefficient maps, nonwidening bounds and containment of all four fixed known probes.

This qualifies a short numerical component, not recording-length prediction ranges, an aircraft observation-error law, whole-program rounding or scientific significance. No aircraft measurements or protected ESA outcomes are used. Earlier failed bounds and their targets remain unchanged.

[Frozen scope](PLAN.md) · [Mathematical component](../ilvis0-conditional-remainder/README.md) · [Requirements before aircraft prediction](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).

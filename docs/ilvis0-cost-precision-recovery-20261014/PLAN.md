# Finite precision-recovery plan

Twelve of 21 remaining stretches qualify by saved failure class. Limits: 86 starts and 5532 native sweeps.

- 72 primary fits: all three models and both processing cases, forty fitting evaluations each.
- Two completed controls: forty fitting evaluations each.
- Twelve predetermined repeats: two hundred fitting evaluations each.
- Two diagnostic predictions per start, included in the total ceiling.
- One worker, four total numerical threads; no retries.

The ceiling is approximately **24.9 serial hours**, estimated from the completed paired trial and each selected interval's duration. This is a planning estimate, not a deadline. Warm starts can finish well below the ceiling, as the qualification trial did.

The arithmetic, models and stopping rules are those of the qualified paired trial. Gradient tolerance remains 1e-4; fresh relative objective change 1e-8; position change at most 1 mm axis RMS and 1 cm at any epoch. Repeats and controls require relative objective agreement within 1e-6 and coordinate RMS agreement within 1 cm per axis. These are numerical tolerances, not instrument accuracy claims.

A stretch contributes only after all six primary fits, its repeat and both controls pass. Failed original checks remain recorded. No result is chosen by taking the lowest cost from repeated starts. The stationary/position-failure strata remain excluded. Every retained source, selected interval, dependency, runtime environment and native kernel is hashed in the new freeze.

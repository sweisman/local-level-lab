# Small exact-arithmetic bound operations dominate the profiles

Both shortened bounds complete. Profiled calculation times are nearly identical:
16.99 seconds with the specified field and 17.07 seconds with zero field.
These shortened physical-domain probes include profiler overhead and are not
full-history performance estimates.

The hot paths are repeated local increments, vector/matrix bound actions,
scalar products, rational construction and arithmetic, and exact matrix norms.
Matrix/vector actions account for about 3.9 seconds of cumulative time per
probe; rational construction accounts for about 4.0 seconds. Cumulative times
overlap and must not be added as independent shares. Clock integration is not
among the leading costs in these probes.

The next implementation will accelerate conservative bound arithmetic while
keeping the exact calculation as an independent reference. Increasing time
limits would leave the scaling problem unresolved. These profiles make no
scientific model comparison; the 53-stretch aircraft findings are unchanged.

[Profiles](README.md) · [Implementation plan](NEXT_PLAN.md) ·
[Saved-baseline screen](../ilvis0-transport-range-preflight/README.md).

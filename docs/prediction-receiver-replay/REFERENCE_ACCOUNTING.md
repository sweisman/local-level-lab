# Preserve the first reference replay's rejected results

The first replay omitted the required scientific-abstention field in
its per-seed result. The sealed record preserves 13 charged seed tasks,
459 checks and 17,085 bound steps. The cooperative stop prevented the
remaining 286 seeds from starting. No model fits or validation cases
were opened.

The separate version 2 replay adds the missing field and requires a
software test that seals a complete result through the actual runtime.
It uses only the 286 unstarted seeds and the same source calibration
archive, forecast score, start selection and scenario definitions.
Use two workers at one thread each with a new 30-minute maximum.
The elapsed time in the first run suggests one worker could exhaust
that allowance before reaching all remaining seeds. Preserve
the first run's failures and count all 13 unavailable seeds in each
original 299-seed scenario denominator. No outcomes are promoted or
discarded because of the accounting repair.
[Original plan](REFERENCE_PLAN.md)

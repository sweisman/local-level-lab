# Final-stretch zero-field timing profiles

The final stretch's specified-field fits now pass both processing-case endpoint
and repeat checks. Its zero-field fits still use time alignments about
57 milliseconds apart, with different costs beyond the repeat tolerance.

This [bounded study](PLAN.md) tests both exact saved offsets from both original
starting solutions, separately under both processing assumptions. Timing stays
fixed only within each diagnostic fit; every other permitted parameter is fitted.
Two fresh controls run before the eight conditional fits.

The ceiling is **654 native evaluations** across ten identities, using four
total numerical threads and no retries. Exhausting the ceiling would take
roughly 5.8 hours at the preceding study's throughput; profiles can stop earlier.
Original observations, bounds, weights and clock remain unchanged.

These profiles cannot change the stretch's disposition. Even successful fixed-time
results need a separate full free-time test, the required repeats and complete
model review. Current findings remain **52 globe / 0 flat / 1 unresolved**.

[Completed field-endpoint study](../ilvis0-last-field-boundary-20261018/README.md) ·
[Current status](../CURRENT_STATUS.md) · [Next analyses](../NEXT_STEPS.md).

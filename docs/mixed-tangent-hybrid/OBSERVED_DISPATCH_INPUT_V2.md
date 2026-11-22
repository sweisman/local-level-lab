# Correct the solver input clock check

The [first input preparation](OBSERVED_DISPATCH_INPUT_PLAN.md) stopped
before decoding any measurements. Its exact selection check compared
the window in memory with the saved JSON. JSON represents the excluded
index pairs as arrays. The old check treated those arrays and the
in-memory pairs as different even though they contained identical
indices.

Compare the canonical JSON bytes on both sides. The software test also
checks that changing an index still fails. Keep the same clock receipt,
original file hashes, window, sampling and artifact limits. Preserve
the original sealed failure. This separately prepared job uses one
thread, a five-minute cooperative limit, zero fits and no reserved data.

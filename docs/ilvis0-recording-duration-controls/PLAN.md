# Eight-minute inputs with explicit clock uncertainty

The earlier representative prediction plan covers 438 seconds. Four-minute
inputs cannot qualify that complete history. This separate software preparation
extends the existing analytic generated-input recipe to 96,000 packets at
200 Hz, about eight minutes. It preserves the original 48,000-packet prefix
bit for bit, including signed values, periods and all physical configuration.
No aircraft measurements are extended, interpolated or changed.

Declare a new clock-offset limit of **±1 second**. All other physical calibration
limits, initial conditions and processing assumptions stay as in the original
broad cases. This clock range is a qualification assumption, not a measured
instrument specification. Preserve the old fixed-clock studies unchanged.

## Component and API checks

First check the input recipe, prefix, duration, retained calibration columns,
clock declaration, provenance and invalid-input rejection with cheap deterministic
tests. Use a supplied parent artifact hash; never label new synthetic suffixes
as measurements from the parent file.

Then compare the old and current native argument interfaces for all three
candidates and both processing assumptions. Query 438 seconds at a normalized
clock value of −1, and 478 seconds at a normalized clock value of +1. The second
point also changes the other calibration coordinates by the same fixed small
pattern used in the earlier compatibility study. Both queries retain full
±1-second clock support within the new input. Compare positions, all 27 Jacobian
columns and warning bits exactly; require a nonzero clock column.

Both callers use the same compiled kernel. Agreement tests the interface and
duration/clock handling, not independent physics or a nonlinear uncertainty bound.
Generated positions from this kernel must not become independent physical truth.

## Finite allowance

Six identities, four native calls each, **24 calls / 2,304,000 maximum packet
visits**, zero interval-bound calls, optimizer starts or aircraft reads.
One worker and one numerical thread. Estimated two to four minutes, with a
fixed ten-minute cooperative ceiling and no retries or signals. Freeze the
generated suffix, parent hashes, complete sources and numerical environment
before launch. Failed cases remain failed.

Success makes complete-horizon software inputs available. Useful bounds derived
from their own training observations, an adequate shared observation-error law
and supported numerical treatment still precede new aircraft prediction fits.

[Recording-length requirements](../ilvis0-three-source-complete/NEXT_PLAN.md) ·
[Completed growth screen](../ilvis0-recording-growth-screen/INTERPRETATION.md).

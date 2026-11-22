# Correct work accounting for the four-time Nuuk comparison

The [original scientific plan](ESA_NUUK_GROUND_PHASE_PLAN.md) remains the
basis for this comparison. The first worker stopped before reading any
observations. The ledger rejected its request to charge eight operations
at once. It recorded zero charged work and saved no scientific output.
Preserve that terminal receipt.

Use a separate frozen task for the corrected worker. Keep the same input
bytes, four times, eleven satellites, range model and 90-second cap. Charge
one setup operation, one for each of four modeled epochs, and one for each
of three range comparisons with their omission checks. The totals remain
eight operations and 169 steps. Verify the original zero-work record and
each retained input hash before the new task can run. No receiver or inertial
fit is part of this work.

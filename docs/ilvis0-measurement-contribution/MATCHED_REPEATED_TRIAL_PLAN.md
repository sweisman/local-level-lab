# Check repeated rejected proposals without relaxing the stopping rule

Audit the seven sealed preflight training traces. From the historical
solver source, a full bounded proposal is computed solely from the last
accepted point and its residual and Jacobian. A rejected local step
changes the trust radius but leaves those inputs fixed. Count repeated
rejected full proposals only when the recorded cost, prediction and
step length match and a separate candidate evaluation was charged.

Add an opt-in proposal rule to the current trust-region solver. Skip a
full proposal only when it is byte-for-byte identical to a full proposal
previously rejected at the same accepted point. Continue the regular
local step and clear the record after every acceptance. Keep the
original candidate limit, bounds, acceptance thresholds and fresh
full-precision stopping checks. Record skip evidence separately from
actual evaluations. Existing callers use the original policy.

Qualify the implementation on known optima, a curved control with a
repeat, the value-only provider and a forced physical stopping failure.
Compare final costs and parameters and verify that independent fresh
evaluations still occur. This turn starts no IMU8 fit. The active IMU21
continuation has its own archived source and scientific allowance.

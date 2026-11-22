# Matched short-prefix fit under the two receiver calculations

Reuse the exact sealed 120-epoch training input from the
[native physical-Jacobian check](STRUCTURED_RECEIVER_NATIVE_RESULT.md).
The recorded IMU increments and earlier receiver positions are identical
for both tasks. Neither task has a later receiver position or scoring input.

Fit the specified-field globe model at the header-elapsed clock, with the
same `h1_v3_tau60` assumed receiver law, all 26 calibration parameters,
identical physical bounds, zero start, ordinary stopping rule and at most
200 charged native tangent evaluations. One task uses the original dense
covariance. The other uses its algebraically equivalent structured operator.
After each fit, charge one more native call to save the fitted trajectory on
the **training** epochs only. Compare both saved fit outcomes and paths in a
read-only report after the two tasks seal.

A software pass requires **both** fits to meet their own original numerical
stopping checks, relative training-cost difference at most `1e-6`, and
maximum fitted-path separation at most **1 cm**. A failed fit remains failed;
do not pick an alternate start, increase its allowance or call a close cost
converged. These tolerances check computational substitution on this prefix,
not the adequacy of the assumed receiver error law.

Freeze two task identities, at most 201 native calls per task, exact
packet-visit limits, two one-thread workers and one hour of cooperative wall
time. Require source-bound software tests and the qualified reboot-recovery
runtime before launch. A verified interruption permits one separate
continuation attempt per unfinished task, at most two technical interruptions
overall, another one-hour wall limit and a 5 GiB free-space floor. Sealed
results, including numerical failures, are never rerun.

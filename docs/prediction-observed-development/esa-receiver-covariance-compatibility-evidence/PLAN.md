# Check whether the receiver terms fit inside the existing forecast covariance

The [receiver difference comparison](ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
retains separate receiver covariances as a development candidate. The
working forecast covariance already includes receiver error. Adding a
second receiver covariance without accounting for the original could
count the same source twice.

For each omitted window in both input conventions, rebuild the fixed
working covariance from the saved forecast and donor settings. Verify
the original quadratic score and log determinant. Map the donor-only
receiver matrices back to the 120 time slots using the same orthonormal
cosine basis. Leave the constant mode at zero because the receiver
comparison modeled it separately.

Subtract the modeled `air1` component from the working `air1` covariance.
Check the minimum generalized eigenvalue of the remaining covariance
relative to the working covariance. Report the maximum nonnegative
multiplier of the `air1` component compatible with positive
semidefiniteness. Treat a multiplier below one as incompatibility for
the complete candidate. Do not shrink the component to make it fit.

Where the candidate fits, substitute each of the two alternate components
in the remaining covariance and score the same sealed forecast and
matched positions. Keep the original degrees of freedom as a descriptive
reference. Report incompatibility and missing results alongside every
completed comparison. The apparent common remainder may mix flight
forecast errors and GPS errors shared by all three receivers. It does not
measure either separately and cannot open reserved flights.

Use the clipped receiver matrices as saved by the donor fit. The ridge
used to score receiver differences remains unassigned. Work in the
fixed forecast's whitened coordinates to check the covariance subtraction.
Keep the full range of the generalized eigenvalue, with no rounding or
increased variance to pass. A singular substituted covariance cannot
receive a predictive score.

Freeze both previous reports, the selected receiver differences,
forecast inputs, donor fits, code, tests and numerical environment.
Use eight pairs of two windows on two one-thread workers, at most eight
bound calls and ten charged steps per pair, no trajectory fits or new
original reads, and a 180-second cooperative allowance. Recover only
unfinished tasks with at most one additional attempt each and a separate
180-second allowance through the verified recovery runner.

# Position and velocity trends on the same receiver windows

The position-derived motion calculation passed its generated-data qualification.
This separate receiver-only diagnostic uses development recording 187 and the
same 2,048 row indices as the completed velocity diagnostic. Unsupported centers
have no replacements. It creates no new eligible cohort.

## Fixed procedure

Verify the original GNSS-only PPP file's hash and byte size against its retained
source reference. Its public reference records the identity and hash; the full
original stays in the retained corpus. Verify the full strict receiver schema
and at least ten decimal places in latitude/longitude and millimetres in height.
Reject unsupported precision or corruption rather than changing measurements.

Use complete, bracketing receiver coverage of each closed ±5-second window,
with no sequence breaks or gap above 0.75 seconds. The actual epochs inside
the window, rather than invented endpoint samples, determine the cubic fit.
Preserve actual support, source indices, unsupported cases and original row times.

For each supported window, run the qualified position method once. The Gaussian
failure allowance is 0.01. Compare independent errors, a supplied half-second
correlation of 0.8, and arbitrary temporal correlation. Retain full within-epoch
covariance and the fixed chart rounding bounds 1e-5 m, 1e-5 m and 0.0005 m.
The supplied correlation is a sensitivity assumption, not an estimated fact.

Compare course rate and north/east velocity with the previous velocity diagnostic
and mean reported velocities over the same window. Report median reported
position/velocity standard deviations and vertical motion separately. Compute
cubic residuals independently with a four-column least-squares calculation;
require RMS agreement within 1e-8 m, a numerical limit rather than sensor accuracy.
Report per-axis residual RMS and lag-one correlation, with correlation unavailable
below a declared 1e-9 m numerical floor.

Keep the old airborne/support classification for paired descriptive summaries.
Do not select a new subset using the new course estimates. Report how often
trend intervals lie wholly within ±0.02°/s, exclude zero speed, or remain ambiguous.
No instantaneous-motion envelope is supplied: a quiet trend is not a guarantee
that the aircraft stayed quiet throughout its window.

## Finite allowance

One identity, one receiver file, at most 100,000 decoded epochs and 2,048 charged
windows. Each window reserves at most one position assessment, one point
kinematic conversion and one independent residual fit. Unsupported starts stay
charged. One worker uses four numerical threads, with a 300-second cooperative
wall ceiling. Zero raw-IMU reads, native trajectories, Earth-model fits,
protected confirmation reads, retries or expanded allowances.

Freeze the source reference, earlier center list, qualification receipt,
confirmation policy, implementation and environment before launch. Each window
and its three stage allowances must be saved before work. Publish all outcomes,
reservation accounting and the paired CSV. A failed numerical check is preserved;
it does not authorize a replacement window or retry.

These results describe receiver consistency under error assumptions. They do not
calibrate real covariance, change selection, establish an independent instrument
replication or affect the 53 completed aircraft model comparisons.

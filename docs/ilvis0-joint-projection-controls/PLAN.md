# Matrix-free joint-error summaries

Check the shared joint-error operator's inverse covariance factor, transpose
and covariance projection. These operations support fixed training averages
and trends while retaining time and cross-axis correlations. They propagate a
supplied law; they do not estimate it or qualify an observed-flight inference.

Use the existing independent dense joint covariance as the small reference.
Keep the cross-axis receiver covariance, two correlation components, shared
offset/drift and nonisotropic inertial noise from the operator controls.

| Identity | Epochs | Probe columns | Fixed summary rows |
|---|---:|---:|---:|
| Small | 5 at 2, 10, 30, 180, 290 seconds | 27 | 12 |
| Long | 64,080 at half-second spacing, starting at 2 seconds | 2 | 12 |

Generate probe arrays with seed 57. The summary rows are four Legendre
polynomials of time on each axis, normalized by their discrete vector lengths.
Retain their full covariance; they need not be mutually orthogonal. They are
fixed independently of observed values and errors. Save source/environment,
recipe, generator hashes and the small projected covariance, rather than large
regenerable probe arrays.

The small case must match dense inverse-factor, transpose and projection
calculations with relative tolerance 3e-10 and absolute tolerance 2e-10. Both
cases must satisfy a relative inverse-round-trip error of 1e-6, maximum error
1e-4, transpose duality backward error 1e-10, and projected positive-semidefinite
slack 1e-10 times the spectral scale. These are numerical software tolerances,
not instrument accuracy or scientific confidence limits. Do not clip eigenvalues.

Accounted array workspace must be at most 128 MiB, including the temporary
transpose factor. Record process peak RSS separately. The long case must not
construct a full observation covariance; storage must remain linear in epochs
for fixed state and summary dimensions.

Freeze two starts with one worker and one numerical thread and a **300-second
cooperative ceiling**. Check the clock between phases and let individual calls
finish without signals. Native calls, packet visits, bound evaluations, original
reads and optimizer starts are zero. No retries or allowance expansion.

Passing qualifies these operations under the supplied constant-coupling linear
law. Nonlinear calibration, uncertain clocks, certified floating bounds and
observational coverage remain separate. Neither aircraft results nor protected
ESA data change. Publish failures as well as successes and archive duplicate
source/input/evidence copies with verified aliases.

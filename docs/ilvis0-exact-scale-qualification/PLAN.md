# Exact shared-error arithmetic: finite qualification

Qualify the fixed Gaussian-law calculation separately from receiver accuracy.
Eight small controls compare exact state-space quadratic forms with independent
rational Gaussian elimination, including missing covariance components and a
perfectly correlated OU state. Eight generated prefixes test 32, 64, 128 and
292 uniformly spaced epochs under each of two predeclared discrete covariance
laws. Their transition coefficients are exp(-1/10) and exp(-1/300), rounded to
the nearest 24-bit dyadic number. These are explicit discrete laws, not exact
continuous-time kernels.

Each identity verifies an integer-only inverse-moment lower-tail certificate
and an exactly checked outward square-root endpoint. A fixed degree-seven
polynomial reference uses known generated coefficients. Unit controls also
test extreme scales, rank overcounting and cooperative resource failures.

Limits: **16 identities, 1,072 total innovation epochs, zero native evaluations,
zero optimizer starts and zero archive reads**. Each identity reserves at most
292 epochs, 131,072 numerator/denominator bits, and ten cooperative seconds;
the whole study has 120 seconds. One worker reserves four numerical threads.
There are no retries, budget expansions or process signals. Charge each
identity and its entire epoch reservation before calculation. A failure stops
the remaining sequence and remains recorded.

Acceptance requires exact dense agreement on all small controls, nonnegative
quadratic forms, valid exact quantile certificates and outward endpoints, and
completion of every prefix within its frozen limits. A pass permits preparation
of a separate training-only recorded-source assessment. It does not validate
Gaussian receiver errors, cure broad nonlinear prediction bounds, authorize
observed Earth-model fits or touch protected ESA groups.

[Overall source plan](../ilvis0-shared-training-error/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

# Bounded prediction software qualification

Qualification **passed**: 8/8 identities, 73.37 seconds. No archive reads, model fits or native integrations.

| Generated control | Simultaneous coverage | Unsupported | Exact 99% lower bound |
|---|---:|---:|---:|
| fixed linear | 511/512 | 0 | 0.9871 |
| boundary linear | 512/512 | 0 | 0.9910 |
| unidentified 27 | 512/512 | 0 | 0.9910 |
| bounded nonlinear | 512/512 | 0 | 0.9910 |
| adaptive design | 508/512 | 0 | 0.9775 |
| finite covariance union | 512/512 | 0 | 0.9910 |

Long-record forecast: 64,080 epochs, 27 columns; 22.98 MiB cached, 197.44 MiB process peak. Marginal-variance identity maximum error 2.53e-14.

These tests assess a declared Gaussian error family and independently bounded mean errors. They do not calibrate archive uncertainty, verify a global nonlinear remainder for the aircraft integrator, or establish withheld physical adequacy. Unsupported cases count as misses. No future observations enter envelope construction.

[Mathematics](MATHEMATICS.md) · [Frozen limits](CONTROL_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

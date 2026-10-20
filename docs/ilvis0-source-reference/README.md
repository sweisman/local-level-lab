# Source reference and affine-error comparison

6/6 generated source reference checks passed.

| Candidate / removal | Coefficients agree | Old remainder (m/s²) | New affine radius (m/s²) | Ratio |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Yes | 0.003048929 | 0.0009680818 | 0.317515 |
| Globe with specified field / profiled | Yes | 0.003048929 | 0.0009716455 | 0.318684 |
| Globe with zero field / zero | Yes | 0.003048929 | 0.0009443115 | 0.309719 |
| Globe with zero field / profiled | Yes | 0.003048929 | 0.0009514409 | 0.312057 |
| Flat disc / zero | Yes | 0.003048929 | 0.0009321741 | 0.305738 |
| Flat disc / profiled | Yes | 0.003048929 | 0.0009410166 | 0.308638 |

6/6 source affine radii improve on the actual saved remainder. Elapsed 11.64 seconds. Reserved 9600/9,600 compiled-source visits and 9600/9,600 independent visits.

Every source retains all 27 physical columns. Coefficients are compared with an independent quaternion/analytic-Jacobian implementation; local tests also use complex-step matrix exponentials. Exact packet endpoints retain the native preceding-packet slope. The affine radius uses the actual compiled-source center and row, not an assumed exact derivative.

This qualifies a mathematical source component only. The source-only C++ exposure uses unchanged native primitives; the complete trajectory consumer has not been replaced or qualified. Floating-point execution enclosure, full position prediction and observational coverage remain unqualified. No aircraft data, protected ESA data or fit was used.

[Frozen scope](PLAN.md) · [Earlier value preflight](../ilvis0-source-norm-preflight/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

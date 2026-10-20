# ESA engineering-rate qualification

48/48 generated controls pass; state: complete.

Analytic component integrals are checked under left-hold, right-hold and linear-point hypotheses. Independent rotation/force ODE solutions check the local body approximation bounds. No actual sampling phase, coning compensation or instrument processing is inferred.

| Family | Completed | Passed |
|---|---:|---:|
| quadrature | 36 | 36 |
| body | 12 | 12 |

Reported rates remain original observations; constructed increments remain labeled calculations. The body bounds assume linear point samples and exclude geographic transport, gravity, antenna motion and cross-interval accumulation. No source recording was reread, no selection changed, and no model fit or protected confirmation evaluation ran.

Reserved 1152 component intervals, 24 ODE solves and 24000 RHS evaluations; elapsed 1.86 seconds.

[Adapter and source distinctions](../esa-rate-adapter/README.md) · [Frozen plan](source-freeze/docs/esa-rate-adapter/PLAN.md) · [Body-bound derivation](source-freeze/docs/esa-rate-adapter/BODY_BOUNDS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

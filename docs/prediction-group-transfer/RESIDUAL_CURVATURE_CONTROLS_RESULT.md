# Residual curvature improves one solver control but leaves the gate open

Using the residual curvature in the step calculation improved the
generated comparison from **4/8 to 5/8**. The analytic and
finite-difference versions passed the same cases. Neither method met
the all-eight requirement, and neither qualifies an aircraft run.

| Generated problem | Saved current solver | Analytic curvature | Finite differences |
| --- | ---: | ---: | ---: |
| Curved interior | 0/2 | 1/2 | 1/2 |
| Upper bound | 2/2 | 2/2 | 2/2 |
| Lower bound | 2/2 | 2/2 | 2/2 |
| Weak direction | 0/2 | 0/2 | 0/2 |

The analytic arm used 136 residual evaluations. The finite-difference
arm used 275, including gradient probes. Both used the original
40-call cap per start and the same fresh position and stationarity
gate. All 16 results and 411 evaluations are sealed.

## Why a reported zero cost gap can still fail

Three failed endpoints had the same reported binary64 cost as the
known solution. An exact evaluation of the generated formula at
the saved parameters resolves a positive gap in each case. The
fresh probe's stationarity threshold is 0.0001.

| Saved failed endpoint | Actual cost gap from the exact formula | Gap as share of one binary64 cost increment | Stationarity at the fresh probe |
| --- | ---: | ---: | ---: |
| Interior, analytic | 1.74 × 10⁻¹⁵ | 0.00383 | 0.000799 |
| Interior, finite differences | 1.75 × 10⁻¹⁵ | 0.00384 | 0.000800 |
| Weak, analytic | 7.71 × 10⁻²⁰ | 2.12 × 10⁻⁸ | 0.111 |

The weak-direction probe moved 1.35 in normalized parameter space,
although its starting point was within 1.4 × 10⁻⁹ of the known
solution. The other weak failures were farther from the optimum.
These outcomes distinguish position and stationarity verification from
agreement in rounded cost. They also show why stable subtraction of
two already rounded residuals can still miss the improvement.
A subsequent software test should preserve the small residual
changes when they are formed and keep the fresh gate unchanged.

The exact diagnostic uses the saved parameters and the known
generated residual formula for the interior optima. For
`d = x - x_opt`, the gap is
`(q*d²)*(2*c + q*d²) + (25*(y - y_opt - b*d²))² + (s*d)²`.
The constants are the frozen control inputs. This calculation uses
no new fit and supplies no evidence that the original aircraft
failures have the same cause.

Six focused tests passed. The earlier solver results are preserved.
No aircraft fit ran and no reserved group was opened.

[Frozen plan](RESIDUAL_CURVATURE_CONTROLS_PLAN.md) ·
[Verified dispositions and completion record](residual-curvature-controls-result.json)

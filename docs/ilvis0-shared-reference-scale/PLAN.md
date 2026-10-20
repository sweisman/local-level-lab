# Fixed-reference shared-scale qualification

Qualify the separate noncentral-dominance scale bound in
[Mathematics](MATHEMATICS.md), using generated inputs only. The existing
bounded-mean method and all archived results remain unchanged.

Eight frozen families, 1,024 realizations each: central residuals; large means
inside the reference space; small noncentral residuals; large incorrect means;
zero reference rank; dependent and absent reference columns; correlated
observations whitened by a supplied independent covariance; and a smooth mean
not represented by the fixed reference. Preserve all 27 columns where present.

Each realization has a fixed true scale and a 0.01 lower-tail allowance. Report
coverage, upper-bound width, unsupported frequency and the exact one-sided 99%
coverage lower limit. The finite qualification gate is a lower limit at least
0.97 in every family, with no unsupported realizations. This is a Monte Carlo
software gate around nominal 0.99 model coverage, not a 0.99 empirical coverage
claim or an assessment of the airborne error law.

Separately verify the noncentral/central lower-tail ordering at fixed thresholds,
the known scalar formula, numerical allowances, rank-zero/rank-deficient designs,
and rejection of adaptive references, unknown noise laws, unknown arithmetic
allowances and saturated reference rank. No candidate fit, future observation
or receiver archive enters the calculation.

Finite ceiling: eight identities, 8,192 generated realizations, 8,192 scale
assessments, 120 cooperative seconds, one worker/four numerical threads. Zero
archive reads, optimizer starts, native integrations or retries. Reserve each
identity's full allowance before executing it. Preserve all failures and charges;
no signals. Freeze sources, deterministic seeds and numerical environment.

Successful software qualification would still leave covariance-shape adequacy,
selection, non-Gaussian errors and the native global-envelope limitations open.
This does not authorize a significance claim or make any protected ESA outcome
available for development.

[Roadmap](../ANALYSIS_ROADMAP.md).

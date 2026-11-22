# Weak-direction tangent probes pass all eight generated controls

The estimated-curvature solver passed **8/8** with the existing
40-evaluation cap and fresh convergence gate. The previous
coordinate-wise estimate passed **6/8**. The new estimate recovered
both weak-direction starts, landing on their known parameters.

| Generated weak start | Full coordinate differences | Weak tangent probes |
| --- | ---: | ---: |
| First | Failed at 40 evaluations | Passed at 34 |
| Second | Failed at 40 evaluations | Passed at 33 |

The full eight-case check used **262 residual evaluations**, down
from 275. The two weak starts used nine weak-direction estimates
each. The other six retain the standard difference path and all
pass. Eleven focused software tests passed.

The next size check uses an existing generated flight fit. Its
saved 45 × 26 tangent has **15 weak directions** at the same
threshold. A single estimate would cost 30 extra tangent calls
there, or 52 if the estimate falls back to coordinate differences.
The saved matrix is at the fitted point, so the split could be
different earlier. A separate flight-scale test must count those
probes and keep the later positions out of training. It must also
account for the fact that the direct residual increments used in
these controls come from a known analytic formula.

This result qualifies the eight generated cases. No aircraft fit,
forecast, or reserved-flight read occurred. The observed solver
and the independent-aircraft validation gate remain unchanged.

[Frozen plan](WEAK_TANGENT_CURVATURE_PLAN.md) ·
[Verified dispositions and charges](weak-tangent-curvature-result.json)

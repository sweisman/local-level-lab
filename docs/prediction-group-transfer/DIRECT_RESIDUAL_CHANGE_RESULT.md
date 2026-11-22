# Direct residual changes recover the two curved-interior starts

Computing trial residual changes before rounding improved each
curvature method from **5/8 to 6/8** on the fixed generated controls.
Both recovered the remaining curved-interior start. Both weak-direction
starts still failed, leaving the qualification open.

| Generated problem | Analytic curvature | Finite differences |
| --- | ---: | ---: |
| Curved interior | 2/2 | 2/2 |
| Upper bound | 2/2 | 2/2 |
| Lower bound | 2/2 | 2/2 |
| Weak direction | 0/2 | 0/2 |

On the recovered start, the two methods reached the same trial
predicted decrease as in the preceding run. The ratio of actual to
predicted decrease had been about **0.0021**, below the unchanged
0.1 threshold. The direct calculation recovered ratios close to
**1.0**. The rounded residuals did report a positive reduction for
those trials. They underestimated its magnitude by about a factor of
480. No accepted trial had a rounded reduction of zero or less.

The four weak cases hit their 40-call cap and retained the earlier
fresh-position failures. The discrepancy on the recovered control
therefore has a specific explanation, while precision in the trial
cost alone does not solve the weak case. These results justify
checking how the optimizer follows the coupled residual direction.
They do not establish the cause of the saved aircraft failures.

All 16 starts and 404 residual evaluations are sealed. Eight
software checks passed. The default observed solver and the fresh
convergence gate stay in use. No aircraft fit or reserved-flight
read occurred.

[Frozen plan](DIRECT_RESIDUAL_CHANGE_PLAN.md) ·
[Matched dispositions and completion record](direct-residual-change-result.json)

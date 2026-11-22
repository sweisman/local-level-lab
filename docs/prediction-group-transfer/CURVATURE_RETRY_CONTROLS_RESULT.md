# Shorter curved steps did not improve the solver qualification

The candidate that tries a curvature-guided fraction of a rejected
solver step passed **4 of 8 generated cases**, the same four as the
current solver. It accepted a fractional step on each of the four
cases that ultimately failed. Accepting those steps did not lead to
the known solution and the required fresh position check within
the evaluation allowance.

| Generated problem | Current solver | With the optional retry |
| --- | ---: | ---: |
| Curved interior | 0/2 | 0/2 |
| Upper bound | 2/2 | 2/2 |
| Lower bound | 2/2 | 2/2 |
| Weak direction | 0/2 | 0/2 |

On the four hard cases, the candidate accepted 16 to 18 fractional
steps and finished with larger parameter errors than the current
solver in all four. Its final stationarity check failed before a
position probe. The current solver reached smaller parameter errors
yet failed the unchanged fresh position check on those four cases.
This gives a reason to test a method that corrects the direction of
the step through coupled curvature. Shortening the same direction
alone did not qualify.

All 16 outcomes and 360 evaluations are sealed. Forty-five focused
software checks passed, including a known one-dimensional case in
which the same retry does reach the solution. The larger qualification
failed and the current solver remains the default. The four original
aircraft fit failures remain recorded. No aircraft measurement or
reserved flight was used.

Regenerate the report from the saved fits without fitting again:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.curvature_retry_study report
```

[Frozen plan](CURVATURE_RETRY_CONTROLS_PLAN.md) ·
[All dispositions and completion record](curvature-retry-controls-result.json)

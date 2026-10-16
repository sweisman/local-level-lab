# Stopping-gate audit of all six unresolved stretches

This audit uses only saved endpoints, receiver epochs and independent mathematical controls. **No original recordings, native predictions or observed fits.** The tally remains **47 globe / 0 flat / 6 unresolved**.

## What the independent controls establish

| Known case | True minimum? | Small-gradient check | Original final gate | Fresh correction worsens cost? |
|---|---|---|---|---|
| cusp_left | True | True | False | True |
| cusp_right | True | True | False | True |
| smooth_minimum | True | True | True | False |
| constrained_minimum | True | True | True | False |
| smooth_nonminimum | False | True | False | False |

The gate can reject a proven cusp minimum even when its gradient tolerance passes. Its full smooth correction crosses the cusp, increases the objective and moves predictions beyond the fixed position limit. This is a counterexample to treating gate failure alone as proof that the current prediction is unstable or that its objective has not been minimized. The smooth nonminimum also fails, so gate failure alone does not establish a cusp minimum either.

## Saved-endpoint screen

The 100 ns, 1 µs and 10 µs distances describe timing geometry; they do not change any acceptance rule.

| Stretch | Unfinished primary fits | Primary epochs within 1 µs of a packet boundary | Small-gradient checks passed | Worsening fresh corrections |
|---|---:|---|---:|---:|
| `0e73879f98c3b701fd7c42df` | 2 | 669/669, 669/669 | 0/2 | 0 |
| `370cec66878c4c1cf84b4ceb` | 2 | 554/554, 554/554 | 2/2 | 2 |
| `50f24131843071ae9312c082` | 1 | 555/555 | 0/1 | 0 |
| `b4e44ddc0f130ecd45674c78` | 4 | 434/434, 434/434, 434/434, 434/434 | 4/4 | 4 |
| `bb8061a43b4f14b6262ceda1` | 1 | 384/384 | 0/1 | 0 |
| `fd7b81e48a4122b149c4925b` | 1 | 354/354 | 1/1 | 1 |

[Endpoint table and source metadata](endpoints.csv) · [All numerical diagnostics](diagnosis.json). The endpoint table includes every scheduled repeat, including passing repeats paired with a failed primary. Three saved affine corrections are compared for each endpoint. Holding time fixed or limiting a linearized step to its current packet interval is diagnostic; neither verifies a full-model optimum.

## Next decision

Keep every original failure and disposition. Qualify a check that distinguishes genuine nonsmooth minima from incomplete fits before another recovery run. A small independently frozen timing profile with nuisance reoptimization may be needed to validate an archival minimum; saved linear systems alone cannot establish it. No revised stopping rule or fitting allowance follows from this audit.

# Where the faster ESA solver has been checked

Changing solver or starting point changed **none of the 384 recorded accuracy
checks** on the 20-minute ESA development window. The largest change in an
accuracy measure was **0.051 mm**, and the closest result to an accuracy limit
was **1.90 m** away. The audit matched 32 forecasts across eight settings,
using both tested globe models, both processing assumptions and both GPS error
descriptions.

| Forecast horizon after training | Settings meeting all four accuracy limits |
| ---: | ---: |
| 120 seconds | 4 of 8 |
| 240 seconds | 4 of 8 |
| 400 seconds | 2 of 8 |

These are unique settings on a single development window. Each setting has
four paths from the two methods and two starts. The table counts the setting
once after verifying that all four paths have the same accuracy flags.
Agreement between solvers and accuracy against later receiver reports answer
different questions. Both whole-window timing pairs were **1.69–1.72×** faster
in fit CPU time for the selective method.
[Paired forecasts](OBSERVED_DISPATCH_FRESH_RESULT.md) ·
[Accuracy measurements](ESA_DISPATCH_ACCURACY_RESULT.md) ·
[Whole-fit timings](ESA_FULL_FIT_TIMING_RESULT.md)

The tested scope covers the two globe models on this development recording.
The disc and other observed recordings still use the established wide
calculation. Independent-flight qualification remains open.

Two focused software tests passed. The audit uses four archived reports and
performs no fits or aircraft reads. The [evidence scope receipt](esa-dispatch-scope-v1.json)
has SHA-256 `03a246b8c6484b5a6275cbcfb47a1bcf0fe1fd93520cf68d81aeac554381a45b`.
Recompute it from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_scope check
```

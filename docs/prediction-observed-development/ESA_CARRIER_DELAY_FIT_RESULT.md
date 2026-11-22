# Fitting a shared atmospheric delay moves the later GPS path by 29 cm

On ESA development flight 187, a delay correction estimated from the
earlier GPS carrier measurements moved the later two-minute trajectory by
**0.29 m RMS**. The fixed shape score changed from **−7.132 to −7.205**,
with zero as the tie point. The specified-field globe still had the smallest
3D error, about 5.17 m RMS, and met all four position limits in both settings.

| GPS carrier-range residual | Standard atmosphere | After applying the earlier fit |
| --- | ---: | ---: |
| Earlier steps, 9,576 ranges | 3.653 mm RMS | 3.641 mm RMS |
| Later steps, 2,736 ranges | 3.773 mm RMS | 3.756 mm RMS |

The two-term fit estimates an overhead-delay correction of −0.188 m at the
first earlier report and a change of −0.016 m per 400 seconds. Both terms
are numerically distinguishable after accounting for position and receiver
clock changes. Their fitted values describe one linearized model, and the
later residual improves by just 0.45%. Other range errors can produce the
same fitted pattern. The result measures the sensitivity to this correction
on one flight and leaves the actual shared error and cross-flight coverage
open.

The calculation verified the saved satellite geometry and GPS-carrier position
scores, then completed all 1,038 steps in one task with no new inertial fit.
Seven focused software checks passed. Only the opened development flight was
used.

With the archived study available, regenerate the saved report from the
repository root. This command checks the completed task and its charge.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_carrier_delay_fit report
```

[Frozen method](ESA_CARRIER_DELAY_FIT_PLAN.md) ·
[Detailed scores](esa-carrier-delay-fit-result.json) ·
[Execution receipts](esa-carrier-delay-fit-evidence/README.md) ·
[Reproduction bundle](esa-carrier-delay-fit-evidence/bundle.zip)

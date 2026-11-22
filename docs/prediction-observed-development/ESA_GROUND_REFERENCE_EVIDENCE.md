# What the ground references add

The permanent Nuuk station supplies a separate set of satellite range
measurements for ESA development flight 187. Its 17 matching timestamps
provide a check on some errors shared by the aircraft receivers. The work
below belongs to **one development flight**. The Qaqortoq receiver adds a
distant one-second comparison on that same flight. The seven reserved ESA
groups remain closed.

| Question | What the check found |
| --- | --- |
| Did both receivers see the same satellites? | Yes. There were 17 matches at 30-second spacing. Eleven dual-frequency satellite tracks continued across the four times used in the motion test. [Overlap](ESA_NUUK_GROUND_INTAKE_RESULT.md) |
| Could a shared range error hide the first test displacement? | On the measured 90 seconds, adding that displacement increased aircraft-minus-ground range error from 3.55 to 18.90 cm RMS. [Fixed-path comparison](ESA_NUUK_GROUND_PHASE_RESULT.md) |
| Could a different error fit between the samples? | Yes. An error that vanishes at the four ground times can still span the saved score gap. It raises the aircraft-only range residual from 3.77 to 4.74 mm RMS. [Between-sample error](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md) · [Aircraft carrier check](ESA_NUUK_BETWEEN_CARRIER_RESULT.md) |
| Does a correction learned earlier help later? | It lowers the later range residual from 4.38 to 1.92 cm RMS. The implied height adjustment on the saved path falls from 21.62 to 5.19 cm. [Chronological comparison](ESA_NUUK_PHASE_TRANSFER_RESULT.md) · [Position effect](ESA_NUUK_PHASE_POSITION_RESULT.md) |
| Do final satellite products explain the range pattern? | The final orbit and clock change leaves about 3.07 mm RMS of the range pattern required to hide the tested error. [Product comparison](ESA_NUUK_ORBIT_CLOCK_RESULT.md) |
| How accurate must the independent reference be? | The range and position requirements trade off. For example, under the stated motion limit, a 1 mm RMS carrier-error cap would allow roughly 1 m per position coordinate at the six reference times. The caps still need independent evidence. [Accuracy requirements](ESA_CARRIER_ANCHOR_ERROR_RESULT.md) |
| What could one-second observations resolve? | The actual 30-second range totals miss the score-sensitive changes between their endpoints. Ideal one-second coverage could reach 99.98% of the signed carrier weight norm. [Sampling comparison](ESA_CARRIER_SCORE_CADENCE_RESULT.md) |
| What does the distant one-second recording show? | The Qaqortoq comparison covers 98% of the carrier weight norm. The aircraft-minus-ground discrepancy is 2.46% of the saved score gap on those directions. A correction learned earlier moves the later score by 0.31% of that gap. [Distant comparison](ESA_QAQ_GROUND_SCORE_RESULT.md) · [Earlier correction](ESA_QAQ_PHASE_TRANSFER_RESULT.md) |
| How do the two stations compare at the same cadence? | Both corrections improve range agreement over the same three later 30-second intervals. The archived aircraft calculations use different paths and satellite products, so their difference cannot be attributed to station location. [Matched-cadence comparison](ESA_GROUND_CADENCE_COMPARISON_RESULT.md) |
| What happens when both use the same path and satellite products? | The range difference between stations falls from 3.48 to 1.47 cm RMS. Both corrections still improve agreement with the same saved path, while faster errors remain open. [Common-product comparison](ESA_GROUND_COMMON_PRODUCTS_RESULT.md) |
| What still limits the result? | The geometric approximation can be bounded from position and motion limits. The actual aircraft range, anchor and motion errors still need independent bounds. [Geometric bound](ESA_CARRIER_RANGE_REMAINDER_RESULT.md) · [Joint error budget](ESA_REFERENCE_ERROR_BUDGET.md) |

The next measurement is the separate 1 Hz Nuuk Museum file. The tested
intake can check timestamps and tracking continuity as soon as the file is
available. Its usefulness will depend on the actual overlap and the accuracy
of the resulting aircraft positions. [Source and intake](ESA_GROUND_REFERENCE_AVAILABILITY.md)

## Reproduce the evidence checks

The [current evidence index](esa-ground-reference-evidence-v3.json) pins
fourteen sealed calculation reports, two ground intake reports, and the joint
error budget. The public check verifies the hashes and recomputes the range
comparisons, correction, sampling and geometric bounds from saved values.
Run it from the repository root. It needs no original flight or ground archive
download.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.esa_ground_reference_evidence check --version 3
```

With the sealed local studies available, use `check-runtime` in place of
`check`. That verifies source, input and result hashes and the original
zero-work accounting failure. Neither check runs an aircraft fit. The
release lists one development flight and makes no calibrated detection claim.
The [seven-study index](esa-ground-reference-evidence-v1.json) and
[eleven-study index](esa-ground-reference-evidence-v2.json) remain available
with `--version 1` and `--version 2`.

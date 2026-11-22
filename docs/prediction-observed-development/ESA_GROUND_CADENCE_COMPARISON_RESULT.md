# How the two ground receivers compare at 30 seconds

On the same three later 30-second intervals, corrections from **both** ground
receivers improved agreement with the corresponding saved aircraft range
calculations. The earlier one-second Qaqortoq check had shown less than a
1% RMS improvement. The distant station can be useful over longer intervals,
while these samples leave faster errors unresolved.

| Ground receiver | Uncorrected aircraft RMS | Full ground subtraction | Correction learned earlier |
| --- | ---: | ---: | ---: |
| Permanent Nuuk | 2.14 cm | 3.17 cm | 1.97 cm |
| Qaqortoq | 3.60 cm | 2.16 cm | 2.10 cm |

The same satellites contributed 97 range changes across ten earlier intervals
and 28 across three later intervals. The fitted earlier multipliers were 0.576
for Nuuk and 0.859 for Qaqortoq. The ground residuals differed by 3.48 cm RMS
on the later intervals. The two calculations of the aircraft residual also
differed by 3.29 cm RMS. They used different satellite products and saved
aircraft path calculations, so this comparison cannot assign the difference
to separation between stations. It supplies no absolute aircraft error bound.
[Frozen comparison](ESA_GROUND_CADENCE_COMPARISON_PLAN.md) ·
[One-second result](ESA_QAQ_PHASE_TRANSFER_RESULT.md)

The nearby one-second station day would allow a comparison using the same
products and time grid as Qaqortoq. Its coverage still needs verification.
The seven reserved ESA flight groups remain closed.
[Station availability](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The [signed interval table and receipt](esa-ground-cadence-comparison-v1.json)
have SHA-256 `4766fca39254d1b638209f87341a0c4c20209ba8fde6ba341634f51e32c41cd8`.
The check replays three saved reports and uses no original flight files,
new aircraft model fits or reserved recordings.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ground_cadence_comparison check
```

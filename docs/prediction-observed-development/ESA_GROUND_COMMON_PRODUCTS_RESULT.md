# Compare the ground stations on the same aircraft path

At 30-second spacing, both ground receivers improved the comparison with
the saved aircraft path. Using the same final satellite products reduced
the later difference between the two stations' range residuals from
**3.48 cm to 1.47 cm RMS**. Updating the Nuuk calculation shifted its
later residuals by **3.29 cm RMS**. The support was identical before and
after the update.

| Ground receiver | Uncorrected aircraft RMS | Full ground subtraction | Correction learned earlier |
| --- | ---: | ---: | ---: |
| Permanent Nuuk | 3.60 cm | 3.16 cm | 2.70 cm |
| Qaqortoq | 3.60 cm | 2.16 cm | 2.10 cm |

Both columns of corrections used the same aircraft residuals, GPS times
and satellites. The earlier multipliers were 0.784 for Nuuk and 0.859 for
Qaqortoq. Each was fitted on the ten earlier intervals and held fixed on
the three later intervals. The comparison counted 97 earlier and 28 later
satellite range differences.

On these intervals Qaqortoq's correction gave lower range disagreement.
The analysis tests agreement with one saved path. Both stations can still
share satellite errors, and local atmosphere and aircraft antenna errors
remain uncertain. The 30-second measurements leave faster errors open.
The nearby one-second Nuuk Museum data remain pending. No reserved ESA
flight was read. [Earlier comparison](ESA_GROUND_CADENCE_COMPARISON_RESULT.md) ·
[Ground data availability](ESA_GROUND_REFERENCE_AVAILABILITY.md)

Seven focused software tests passed. The worker completed one task and
charged all 14 checks with zero aircraft fits. The [signed result](esa-ground-common-products-result.json)
has SHA-256 `6358a08afcfe4575790ee6b915d927f5e626a728f31d90de15fcb8d91581f758`.
[Frozen plan](ESA_GROUND_COMMON_PRODUCTS_PLAN.md) ·
[Archived evidence](esa-ground-common-products-evidence/README.md)

Reproduce the report from the closed study in the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies check docs/prediction-observed-development/esa-ground-common-products-evidence
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ground_common_products report
```

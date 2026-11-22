# When both NASA shape models use zero background field

The specified-field globe has the lowest fitted cost on all **53**
selected NASA stretches under both saved processing assumptions.
Holding the background field at zero for both shapes asks a different
question. In that comparison, the zero-field globe has lower cost on
**35 stretches** and the disc has lower cost on **18**. The direction
agrees across the two processing assumptions on every stretch.

| Zero-field results among stretches in each recording group | Groups |
| --- | ---: |
| Lower globe cost on every stretch | 17 |
| Lower disc cost on every stretch | 5 |
| Both outcomes within the group | 5 |
| Total | 27 |

The 18 disc-favoring stretches occur in 10 groups. Thirteen carry the
latest saved repeat status `passed`. That flag describes the recorded
numerical checks for the stretch's result. It supplies no separate
flight or repeat measurement. Costs were compared within each matched
stretch and processing setting. Mixed groups retain their constituent
results, with no aggregate vote or pooled cost.

This table describes the original development recordings. Grouping
accounts for known overlap and dependence, while instrument or
processing errors can be shared across groups. Neither the stretch
counts nor the group counts provide calibrated confidence, and the
zero-field comparison does not test both shapes under a specified
nonzero field. The [separate prediction checks](../PAPER_DATASET.md#prediction-evidence-kept-separately)
address different evidence.

## The reserved development pilot

The metadata-selected four-recording pilot includes two stretches with
lower disc costs at zero field and two with lower globe costs. The first
two recordings used for the numerical preflight, one per IMU type, were
both from the disc-favoring zero-field subset. Their later four-candidate
preflight is incomplete because the zero-field disc forecasts are missing.
On those same recordings, the [available specified-field forecasts](../ilvis0-measurement-contribution/MATCHED_FORECAST_RECEIVER_RESULT.md)
favor globe over disc at a matched field. These forecast comparisons
leave absolute accuracy and the complete four-candidate result open.
The cross-check uses past fitted results only to describe the already
reserved pilot. The selection and qualification rules still govern
any future fitting. [Pilot selection](../ilvis0-measurement-contribution/MATCHED_PILOT_CANDIDATES_RESULT.md)
The [one-task continuation](../ilvis0-measurement-contribution/MATCHED_UNSTARTED_DISC_RECOVERY_RESULT.md)
closed the IMU21 slot. At zero field its withheld GPS results favor
globe in horizontal and 3D error and disc in height. The existing IMU8
stopping result is retained.

Verify the ledger from the repository root. Use `write` in place of
`check` to generate missing files. The command checks the original
published cost and grouping hashes and makes no fits. The `pilot`
command adds the check against the sealed pilot selection.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_group_zero_field check
```

[Group ledger](nasa-group-zero-field.csv) ·
[Source hashes and totals](nasa-group-zero-field-receipt.json) ·
[Original fitted comparisons](../CURRENT_STATUS.md)

# The ESA forecast ranking survives scoring north and east alone

Two checks on development recording 187 separate the effect of height
on forecast uncertainty from its effect on the model ranking. They use
different cuts of the same flight.

## After 800 earlier reports

Over the first 120 later positions, the adjustment based on earlier GPS
reduced height RMS from **4.32 m to 1.56 m**. With the same stated height
width around either path, zero raw predictions and **25 adjusted
predictions** contained the GPS height. No position moved out of the
band after adjustment. The standardized height RMS fell from 18.25 to
4.25 times the stated standard deviation.

The adjustment helped at this horizon. The stated width still missed 95
of 120 later heights. This check puts the adjusted widths around the
raw path for comparison and supplies no uncertainty estimate for the
raw forecast. [Original uncertainty check](ESA_MATCHED_UNCERTAINTY_RESULT.md)

## After 400 earlier reports

The specified-field globe had the lowest joint forecast error throughout
both complete model comparisons under all four working covariances. It
kept that ranking when the score used only north and east at the 120
later positions.

| Candidate | Joint squared standardized error, three axes | North and east alone |
| --- | ---: | ---: |
| Globe with specified field | 7.35–11.06 | 3.38–4.00 |
| Globe with zero field | 522–667 | 449–584 |
| Stationary disc | 846–1,043 | 691–890 |

The horizontal calculation retains the correlations between north and
east and across times. All earlier observations and saved forecasts
stay fixed. Two model comparisons remain incomplete after four
disc fits failed their original numerical checks. The result leaves
physical height adequacy and forecast error across flights open.
[Original whole-path scores](ESA_JOINT_PATH_SCORE_RESULT.md)

The first run saved the height comparison. The runner rejected four
ranking tasks before charging any work because it requires individual
charges. A separate run reused those four frozen inputs and charged all
84 calculations. No navigation fit was repeated. Both execution records
and the original failed fits are preserved. The seven reserved ESA groups
remain closed.

[First plan](ESA_HEIGHT_ROLE_PLAN.md) ·
[First run evidence](esa-height-role-initial-evidence/replay.zip) ·
[Follow-up plan](ESA_HEIGHT_ROLE_ACCOUNTING_PLAN.md) ·
[All scores](esa-height-role.json) ·
[Follow-up replay bundle](esa-height-role-ranking-evidence/replay.zip)

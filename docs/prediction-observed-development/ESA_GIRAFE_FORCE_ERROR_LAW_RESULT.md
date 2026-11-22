# A window-wide error term better predicts later force disagreement

We used the first four windows to predict the GIRAFE–iMAR difference
on the last four windows of the same flight. The calculation was
repeated at both averaging widths. The earlier estimated offset was
about **−26 mm/s²** in both cases. The later window means departed
from that estimate by as much as **3.15 mm/s²**.

| Averaging width | Later means inside the independent-noise range | Inside the correlated range | Mean log score, independent / correlated |
| --- | ---: | ---: | ---: |
| 11 receiver reports | 1 of 4 | 3 of 4 | −4.27 / −4.38 |
| 25 receiver reports | 1 of 4 | 4 of 4 | −4.62 / −4.79 |

The correlated model had a lower log score in all eight comparisons.
Its estimated window-wide standard deviation was about 1 mm/s². Its
neighboring-sample correlations were −0.13 and +0.14 at the two widths.
The working 95% ranges for a window mean widened from 1.58 to 2.67
mm/s² and from 1.21 to 2.58 mm/s², measured from the predicted mean.

The eight comparisons reuse four later windows on one aircraft. Both
instruments contribute to the measured difference. The test supports
retaining a persistent error term in development. Absolute sensor
accuracy, independent-flight coverage and the Earth-model decision
threshold remain open.

Both tasks completed and used saved measurements. No additional
recording was read and no Earth model was fitted.
[Frozen design](ESA_GIRAFE_FORCE_ERROR_LAW_PLAN.md) ·
[Scores, covariance matrices and charges](esa-girafe-force-error-law-result.json)

To verify the saved report, restore
`data/esa-girafe-force-error-law-v1` and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_force_error_law report
```

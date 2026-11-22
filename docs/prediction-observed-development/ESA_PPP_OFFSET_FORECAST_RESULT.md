# Recent GPS differences improve offset predictions, with too little uncertainty

The first 97 windows select a mean-reverting model with an 80-minute
persistence time. Carrying an earlier receiver difference forward
improves the short-lead prediction of that difference on the later
98 windows. The fitted uncertainty is still far too small.

| Lead in inventoried windows | Offset RMS, fixed → changing | Mean squared standardized error, fixed → changing |
| --- | ---: | ---: |
| 1 | 38.65 → 6.12 mm | 78.54 → 28.75 |
| 4 | 38.65 → 15.19 mm | 78.54 → 73.67 |
| 12 | 38.65 → 26.83 mm | 78.54 → 96.94 |

The usual elapsed leads are 2, 8 and 24 minutes. A gap between
inventoried windows extends some leads, including one nominal
one-window forecast to 42 minutes. The 97 one-window forecasts at
exactly two minutes still have a mean squared standardized error of
28.62. The gap therefore cannot explain the short-lead undercoverage.
Values near one would indicate agreement with the modeled scale.

The changing model improves the Gaussian log score at one and four
windows, and worsens it at twelve. A better estimate of the mean
offset does not establish reliable prediction uncertainty. These
forecasts need observations from the three GPS solutions and cannot
measure their shared error. They do not qualify another flight.

The task completed in 6.6 seconds, with six software checks, 496
charged calls, and no new aircraft fits or source reads.

[Frozen plan](ESA_PPP_OFFSET_FORECAST_PLAN.md) ·
[Verified evidence](esa-ppp-offset-forecast-evidence/README.md)

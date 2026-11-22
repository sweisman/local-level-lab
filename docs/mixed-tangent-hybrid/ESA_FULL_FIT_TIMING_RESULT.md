# Faster fits on the full ESA development window

The selective derivative calculation passed both timing comparisons on one
ESA development flight. It used 800 receiver positions for training and
evaluated forecasts at 400 later times. The later receiver positions stayed
withheld. Both methods used the same measurements, bounds and starting point
in each comparison.

| Globe setting | Wide fit CPU | Selective fit CPU | Fit speedup | Wide total elapsed | Selective total elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Specified background field | 666.3 s | 394.1 s | 1.69× | 798.3 s | 479.4 s |
| Zero background field | 2,004.4 s | 1,164.6 s | 1.72× | 2,115.5 s | 1,253.5 s |

Both pairs met the original stopping and cost checks and retained every
derivative column. Their computed positions agreed within 0.17 micrometres
across the training and forecast times. The two speed ratios exceeded one
and their median of 1.71× exceeded the planned threshold of 1.25×. The study
charged 76 native calls across both pairs.

This test establishes a timing improvement for these two settings on one
recording. Accuracy on unused positions and performance on other recordings
remain open. [Frozen plan](ESA_FULL_FIT_TIMING_PLAN.md) · [Reproduction evidence](esa-full-fit-timing-evidence/README.md)

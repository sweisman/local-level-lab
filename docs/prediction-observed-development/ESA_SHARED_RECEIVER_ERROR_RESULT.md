# How much could shared GPS error change the ESA result?

In both complete settings, the disc would need a change of at least
**3.22 km RMS** to the GPS path to tie or beat both fixed globe forecasts.
The zero-field globe would need at least **1.30 km RMS** to tie or beat
the specified-field globe while staying ahead of the disc.

The position-accuracy screen is much more sensitive. It could fail if the
GPS path changed by **3.93 m RMS** concentrated at one report, enough to
reach the 50 m peak horizontal limit. Reaching the 10 m horizontal RMS
limit would require at least **4.82 m RMS** of path change.

These numbers use the same 120 later positions on the development flight,
the same local distance metric and the same forecasts. The calculation
allows any shift at each report. It measures how far the recorded path is
from changing a result. It does not estimate the actual GPS error or test
whether a different calibration could change the forecasts. The ranking
and the accuracy screen therefore need different levels of receiver
validation.

The campaign used three receivers on one antenna. Its gravity products
also use the GPS trajectory to account for aircraft motion. They supply
no independent airborne position reference. A nearby fixed ground
station could check some errors shared by the satellite measurements,
while aircraft-specific errors would still need separate treatment.
[Campaign instrumentation and processing](https://essd.copernicus.org/articles/17/1667/2025/)

Three known-answer checks passed. The audit verified the original
reference scores and replayed each smallest path correction. No new
fit or forecast was run. The seven reserved flight groups remained closed.

[Frozen plan](ESA_SHARED_RECEIVER_ERROR_PLAN.md) ·
[Exact corrections, scores and hashes](esa-shared-receiver-error-result.json)

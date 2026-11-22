# Smooth drift can imitate the forecast difference between geometries

In all four available comparisons, a smooth change in position, velocity
and acceleration accounts for more than **99.9% of the squared distance**
between the globe and disc forecast paths. The two paths in each pair use
the same specified background field, including zero in the ESA pairs.
An arbitrary adjustment of those nine terms would remove nearly all of
the separation on these windows.

| Forecast pair | Later reports | Full 3D separation (m RMS) | Smooth part (m RMS) | Remaining separation (m RMS) |
| --- | ---: | ---: | ---: | ---: |
| NASA IMU8, specified field | 223 | 234.48 | 234.46 | 3.24 |
| NASA IMU21, specified field | 148 | 69.54 | 69.50 | 2.11 |
| ESA 187, zero field, increment error description | 120 | 1,441.19 | 1,441.19 | 0.75 |
| ESA 187, zero field, point-rate error description | 120 | 1,441.19 | 1,441.19 | 0.75 |

Four other comparisons remain missing a disc forecast. They are the two
NASA zero-field comparisons and the two ESA settings with the upstream
removal fraction fixed at zero. The two complete ESA comparisons use the
same flight observations with two descriptions of inertial error.

The amount of smooth adjustment needed to absorb the entire smooth
separation ranges from **69.50 m to 1,441.19 m RMS**. The replay assumes
that smooth adjustments could be arbitrarily large. A physical error
model needs to bound them with information independent of the later
positions. A correction shared exactly by both candidates cancels in the
path difference. The bound that matters here is how much the corrections
allowed for the two candidates can differ.

## What changes when the forecast uses earlier residuals?

The [earlier ESA covariance check](FORECAST_PAIR_INFORMATION_RESULT.md)
used forecasts conditioned on the training period. The [matched metric check](MATCHED_SHAPE_METRIC_PLAN.md)
held the same zero-field pair, coordinate anchor and nine smooth terms fixed
while changing the conditioning and weighting separately.

| Forecast means | Full distance (m RMS) | After smooth terms (m RMS) | Full distance under working covariance | After smooth terms under working covariance |
| --- | ---: | ---: | ---: | ---: |
| Raw | 1,442.93 | 0.755 | 27,483.17 | 25.46 |
| Conditioned on earlier positions | 7.24 | 0.758 | 25.45 | 25.41 |

Conditioning on earlier positions removed almost all of the initial smooth
gap. The remaining departure from a smooth path is about **0.76 m RMS** in
both cases. It accounts for **99.69%** of the squared distance of the
conditioned forecasts under the working covariance. The metric check uses
the earlier study's coordinate anchor, which accounts for the small change
between its raw distance and the first table.

The result identifies what a prediction test still needs to distinguish:
sub-metre departures from smooth motion, with uncertainty that reflects
their timing and correlation. The current covariance gives those differences
substantial weight. Its real-aircraft accuracy remains to be established.

The [frozen method](MATCHED_SHAPE_DRIFT_PLAN.md) compared already sealed
training-only forecasts. It read no GPS positions or original recordings
and ran no trajectory fits. Four software checks passed. These path
differences are a test of method sensitivity and do not settle which
geometry fits the aircraft's actual motion under a qualified error law.

[Source and input freeze](matched-shape-drift-freeze.json) ·
[All eight comparisons](matched-shape-drift-result.json) ·
[Matched metric freeze](matched-shape-metric-freeze.json) ·
[Metric results](matched-shape-metric-result.json)

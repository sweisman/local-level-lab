# What the new refits show, and what remains unresolved

The [two selected tracks](TRACKS.md) were chosen by duration and IMU configuration from
the complete saved-artifact set. All twelve full-position reconstruction checks
passed before fitting. All 24 horizontal-only fits then passed their individual
numerical gates. The study used 1,112 native calls and took 3.64 hours.

## The IMU8 comparison is complete

The 9.75-minute recording is `ILVIS0_applanix_55124_Ames_510-20oct09_20Oct09.013`.
All six independently initialized repeat comparisons pass. Both processing cases
favor the globe family after refitting without height contributing to the score.

The specified-field globe has horizontal RMS error about **0.37 m**, compared
with **34 m** for the unsubtracted flat model and **17 m** when the flat model
may profile upstream field removal. The zero-field globe gives about **7.6 m**.
Thus both shape and the specified-field comparison favor the same models as
the preserved full-position analysis. No significance level is assigned.

## The IMU21 comparison remains unresolved

The 4.07-minute recording is `ILVIS0_applanix_55295_20100409_610_LVIS_09Apr10.013`.
All twelve individual fits pass, but only three of its six repeat comparisons do.
Its shape/field interpretation is withheld under the frozen repeatability policy.

Both starts nevertheless rank the specified-field globe first: horizontal RMS
is about **1.4 cm**, compared with **30 cm** for zero-field globe, **17 m** for
unsubtracted flat and **9 m** for profiled-removal flat. The failed repeats are
not evidence of equal model support; they prevent a completed matched result.

The two zero-field globe cases settle at timing offsets near **−84.23 ms** and
**−103.19 ms**. Their costs differ by about 0.16%, and their predicted positions
by several millimetres. Both stops report no further positive predicted decrease.
Neither is especially close to a packet boundary: the nearest distances are
about 0.71 and 1.75 ms. Ordinary and range-scaled affine solves give essentially
the same tiny predicted improvements. This differs from the earlier incorrect
affine-solve failure; rescaling alone does not explain the disagreement.

The unsubtracted flat pair agrees in cost but has north-position RMS difference
about **1.21 mm**, above the **1 mm** limit. Timing is identical at its bound;
gravity correction and weak vertical coordinates differ. Its repeat used all
200 evaluations. The other profiled-removal flat pair passes.

## Height removal permits implausible vertical paths

Unscored height RMS ranges from roughly **0.65 km to 114 km** across the returned
fits. These are residuals against receiver height, not measured changes in the
aircraft's altitude. Removing the vertical score leaves nuisance directions
insufficiently constrained to reconstruct a credible full flight path.

This sensitivity check shows that the completed IMU8 score advantage survives
removing height from the objective, even with that additional freedom. It does
not establish a physically adequate three-dimensional alternative fit. Heights
still enter initialization, covariance and propagation, both IMU channels remain,
and conventional receiver-coordinate construction has not been removed.

The original **53 globe / zero flat / zero unresolved** result uses the original
full-position objective. Its labels are preserved; the unresolved IMU21 sensitivity
check does not overwrite them. No dataset expansion or global-optimum claim
follows. The completed fixed-point diagnostic isolates coupled timing/calibration
and an unobserved vertical direction without changing any acceptance limit.

[Detailed metrics and repeat table](README.md) ·
[Fixed-point results](../ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md).

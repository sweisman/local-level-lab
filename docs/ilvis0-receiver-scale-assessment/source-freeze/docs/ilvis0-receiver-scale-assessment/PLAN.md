# Finite training-only receiver-reference assessment

Assess the first **292 one-second receiver epochs** of the previously studied
IMU21 recording `ILVIS0_applanix_57300_610_LVIS_38614965.013`, segment
`570b37d23af5e245dd461051`. Their 291-second span precedes the withheld positions
in the saved prediction comparison. This is retrospective development of a
common error source, not a new Earth-model comparison.

Verify the original publication receipt before extracting the prefix. Freeze
only those training coordinates, the source hash and the parent-selection hash.
The assessment API cannot receive later coordinates, gyros, fused navigation,
Earth-model residuals or candidate identities. Test that changing every later
coordinate leaves its input unchanged.

Use the fixed affine chart `north = 6371000 × latitude_rad`,
`east = 3185500 × longitude_rad`, and reported height in metres. The longitude
scale is fixed at cos(60°)=1/2, not estimated from noisy latitude. This is a
reference chart, not the older receiver-dependent geographic error metric.
Exact residuals retain the supplied binary receiver-coordinate values.

Report all six predeclared combinations: time-polynomial degrees **3, 5, 7** and
discrete OU correlation families approximately **10 and 300 seconds**. Three
axes are independent under the declared law. White standard deviations are
0.3/0.3/0.7 chart metres; OU, constant-offset and training-anchored drift standard
deviations are each 1/1/3. Their common multiplier is bounded from training data.
OU transitions are rounded to the nearest 24-bit dyadic number. Coefficients
are ordinary numerical least-squares references; their residual quadratic forms
and all tail/endpoint certificates use the qualified exact calculation.

Every bound uses per-assumed-law failure probability **0.01**. Report all
combinations without selecting a covariance using model ranking. No simultaneous
coverage or empirical Gaussian-law verification is claimed. A bad reference
trajectory can inflate a conservative upper bound, so it is not a measurement
of receiver accuracy or a reason to enlarge a candidate's own error allowance.

Freeze six identities and at most **5,256 scalar innovation epochs**, 131,072-bit
rational numerator/denominator limits, ten cooperative seconds per axis, thirty
seconds per identity and 240 seconds overall. One worker reserves four numerical
threads. Charge each identity and its 876-epoch reservation before calculation.
Zero native evaluations, Earth-model optimizer starts, original IMU reads or
protected ESA evaluations. No retries, extensions or process signals.

Acceptance means every exact calculation completes within those limits with a
nonnegative quadratic form and a finite certified endpoint. It does not mean
the declared covariance is physically adequate. Preserve failures and stop the
sequence if qualification fails. Broad nonlinear prediction ranges and absolute
predictive adequacy remain separate gates; no observed Earth-model fit follows.

[Qualified mathematics](../ilvis0-exact-scale-v2/INTERPRETATION.md) ·
[Saved prediction evidence](../ilvis0-saved-prediction-comparison/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

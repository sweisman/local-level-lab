# Fitting with the two ESA receiver-error cases

## Question

Does the shared training/forecast calculation preserve known answers when both
versioned working receiver-error cases replace the earlier simple software
weights? This is the final matched calculation check before the first observed
ESA pilot. It reads no observed recording or protected data.

## Fixed matrix

Reuse the independent Cartesian trajectories, synthetic sensor/antenna errors
and two-minute maneuvering pattern from the completed training controls. Keep
300 Hz samples, 119 queries, the earlier 79 training positions, the later 40
prediction positions, both latitude signs, all three generating geometries,
both upstream-processing cases and both fixed starts.

Add both working error policies. The complete matrix has 48 identities. Each
fit uses its generating geometry; this checks numerical estimation and unused
prediction, not a calibrated winner decision. Synthetic observations remain
noiseless, so reported residuals do not measure actual instrument precision.

For the receiver fixture use north/east/height variances 0.04, 0.09 and 0.25 m²,
with north–east, north–height and east–height covariances 0.01, 0.02 and −0.015 m².
These fixed software values are independent of model residuals and are not
estimates from ESA data. Convert coordinates to the shared receiver chart, and
apply each working policy with actual times and full cross-axis covariance.
No later coordinate or uncertainty value may enter training weights.

Use a shared `lll.airquantumgrav_prediction` pipeline for generated and later
observed fits. It accepts raw arrays and earlier receiver rows only, uses the
existing initializer, estimator and forecast, and saves the forecast before the
caller opens later scoring positions. The caller must retain every nuisance
column and score against the independent Cartesian answer in these controls.

Preserve the preceding training control's calibration domain, two starts and
near-zero/ordinary stopping composition. A pass requires numerical completion,
all 26 or 27 columns, training and prediction horizontal/height RMS at most
0.1 m and maximum spatial error at most 0.5 m. Do not change accuracy limits or
retry a failed start to obtain qualification.

## Finite allowance

There are 48 starts. Each permits at most 200 fitting calls including fresh
stopping checks and one continuous forecast: 9,648 native calls in total.
The conservative packet/query ceiling is 41,332,032,000 visits. Construct
1,728,000 intervals and at most 1,737,552 independent truth samples, charging
before work. Four workers each use one numerical thread, with a cooperative
two-hour ceiling and no retries. Completed allowances cannot expand or fund
replacement runs.

## Qualification and evidence

Bind the exact sources/environment to software checks before launch. Test
training-only weights, later-observation isolation, unchanged raw prefixes,
all columns, covariance caps, fixed identities and resource accounting. Compare
the common pipeline with the existing independently generated controls and
retain every raw fixture, weight description, fit, forecast, score and journal.

Preserve the already completed controls and real interval preparation. Successful
generated checks authorize only preparation of a separately frozen observed
pilot. They establish neither real-data adequacy nor calibrated confidence.
Packaging reads saved results and does not fit or propagate again.

[Original training controls](../esa-training-forecast-controls/README.md) ·
[Prepared observed interval](../esa-development-pilot-preparation/README.md) ·
[Working error policy](../ESA_ERROR_POLICY.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

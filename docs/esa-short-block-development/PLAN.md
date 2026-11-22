# Short-block development selection

This metadata-only selection uses the three additional, nonoverlapping
twenty-minute windows already frozen in the [broader development plan](../esa-broader-development/README.md).
It does not open an IMU or receiver measurement, prepare samples, fit a model,
score a prediction, or touch any reserved confirmation group.

For every additional window, keep its first 800 one-second receiver queries
for training and select the next 120 for a future prediction. Retain the
remaining 280 queries as unused support. Select **all three** windows; do not
choose among them by model outcome. The 120-second duration is fixed from the
[generated horizon calculation](../prediction-observed-development/ORACLE_HORIZON_REPORT.md),
which gives a 2.70 m horizontal RMS scale with earlier receiver updates under
its declared synthetic laws. The [retrospective ESA horizon table](../prediction-observed-development/RECORDED_HORIZON_DIAGNOSTIC.md)
is descriptive and is not an independent basis for selecting a successful
window.

Every row retains the parent run, original receiver indices, source hash and
shared development-group identity. This freeze does not certify actual IMU
support, receiver quality, error-law adequacy or prediction coverage. Those
gates and a separately finite study definition are required before a fit.
The earlier 400-report failure remains unchanged.

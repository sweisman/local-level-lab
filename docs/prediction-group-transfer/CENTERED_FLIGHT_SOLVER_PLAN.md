# Centered solver in the generated flight pipeline

Run one matched pair for each physical candidate through the full native
calibration and withheld-prediction pipeline. Use 24-second generated
histories with 23 receiver reports. Fit the first 15 and score the last
8 against generated positions revealed only after the forecast is saved.
Use the same 26 calibration coordinates, increment error law and zero
background-field removal as the longer independent-optimizer control.
Use the model's own generated truth. This is a numerical qualification,
with no model selection from synthetic outcomes.

Use 300 Hz header time for the specified-field globe and stationary disc,
and exact 200 Hz nominal time for the zero-field globe. Use the model and
clock seeds of the longer control and the zero start for both solvers. The
solver is the only difference within a pair. Compare the existing trust
region with centered L-BFGS-B using the same unchanged final gate.

Prepay at most 200 training evaluations per fit, plus the exact generated
input and prediction workload. Allow six starts with one numerical thread
and a 210-second cooperative wall limit. Preserve any numerical or
technical failure and its charged work. No reserved flight can be read.

A pair qualifies only if both methods pass the unchanged numerical and
separate physical screens, their objective values differ by at most 0.01,
and their withheld position predictions differ by at most 0.10 m at every
report. This short screen checks the complete pipeline before a longer,
more costly qualification. It gives no aircraft deployment authorization.

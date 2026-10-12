# Retrospective prediction trial

This development trial asks whether calibration fitted on an earlier part of
one recording predicts its later GPS track. An IMU (inertial measurement unit)
records turning and acceleration. The IMU drives a continuous predicted track;
the GPS positions in the final portion are reserved for checking that prediction.

The recording has already been examined in full-stretch studies. This is a
retrospective prediction check, not unseen-data confirmation or an independent
flight replication. No scientific decision threshold is calibrated by this trial.

## Target and chronological split

Reuse the entire frozen control `570b37d23af5e245dd461051` from
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21. Its selected interval
is 2015-10-05 12:45:50–12:53:08 UTC, 438 seconds, with receiver ground speed
at least 859.55 km/h and median 878.06 km/h. No interval is selected again.

There are 439 receiver epochs. Fit the first `floor(2*439/3) = 292` epochs,
12:45:50–12:50:41 UTC, spanning 291 seconds. Predict the remaining 147 epochs,
12:50:42–12:53:08 UTC, spanning 146 seconds. A one-second interval separates
the last training epoch from the first prediction epoch. These portions are
parts of one recording, not separate eligible flights or independent trials.
Freeze the exact split from saved receiver timestamps before new predictions.

## Models and allowance

Fit rotating globe, still globe and the existing stationary disc under both
existing processing cases, with ±1°/hour constant gyro offsets and ±2% gains.
These primary bounds are unchanged; do not select a zero-correction ablation
because it produced convenient full-stretch results. Keep packet-header timing,
the original frozen optimizer, mount/lever/initial-state bounds, gravity and
receiver covariance definitions unchanged.

The proposed scope is **six starts, one per identity, at most 200 evaluations
per start, no retry reserve**. Two post-fit native predictions (training-only
and continuous whole-track) are included in each 200-evaluation cap. A fresh
training stationarity check is included by the original solver. Preserve every
failure, interrupted charge and unresolved fit. Do not borrow unused starts
from completed studies or promote a budget-stopped fit using only its gradient.

## Preventing leakage into fitting

Initialization receives training GPS coordinates only and an IMU prefix ending
at the last training epoch plus its existing 0.15-second timing allowance and
the containing original packet. It receives no positions from the prediction
portion. The established seed uses the first ten seconds of these training
inputs; no fused Group-1 attitude/rates are supplied.

The training problem receives only training residuals and the marginal training
block of the full-window declared covariance. The original covariance's drift
fraction remains normalized over the unchanged full window; recomputing it over
the shorter interval would silently change the error assumption. Future receiver
coordinates cannot affect that training covariance block. Future timestamps
define the frozen split/window, not model calibration.

After fitting, decode the same fixed parameters in a continuous prediction from
the initial state to the final epoch, driven by the original IMU increments.
Do not reset the state to GPS at the split, change calibration during prediction,
or use prediction errors to choose another start. Verify that continuous prediction
reproduces the independently evaluated training prefix and training objective.

## What is reported

Keep training and prediction costs separate. Report unconditioned physical
north/east/up errors and horizontal/vertical RMS first, using the same declared
reference coordinate metric as the clock trial. Save per-epoch direct errors
with explicit training/prediction roles, along with calibration estimates,
signed bounds, solver status, fresh gradient, singular values and evaluation counts.

For receiver covariance `C` and training residuals `r_T`, also report prediction
innovations after subtracting `C_PT C_TT^-1 r_T`, whitened with Schur covariance
`C_PP - C_PT C_TT^-1 C_TP`. This conditions the assumed correlated receiver
errors; it does not correct the propagated trajectory or supply GPS updates.
Keep direct errors visible alongside these diagnostics. Apply the same calculation
under the existing conservative covariance without refitting.

These are plug-in diagnostics at estimated calibration parameters. They omit
parameter uncertainty and use assumed receiver covariance. Small normalized
errors do not establish calibrated predictive coverage. Shape-first numerical
profiles are reported separately for training and prediction, using the same
convergence requirements. Reveal rotation only after both processing cases
resolve shape in favor of globe. Preserve unresolved comparisons as unresolved.

## Freeze, runtime and stopping

Freeze sources, input hashes, exact Python/NumPy/SciPy versions, thread settings,
configuration and split. Use one detached worker with two numerical threads,
an exclusive lock, durable start journal and atomic hashed results. Packaging
performs no fitting. Do not resume completed numerical work or retry an
interrupted charged identity.

Based on the previous full-stretch runs, expect roughly **45–75 minutes** if
the six fits use their full allowance, plus preparation/publication. The shorter
training interval should reduce native integration cost; this estimate is not
a measurement of the new trial or a wall-clock guarantee. At the previous
slowest full-window rate, 1,200 evaluations would take about 74 minutes.

The trial has a finite allowance and publishes verified results on completion.
Further fits or archive expansion require a separate study plan and allowance.

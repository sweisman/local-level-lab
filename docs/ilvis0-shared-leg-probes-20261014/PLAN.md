# Shared-leg prediction and tangent checks

This finite diagnostic examines the three unresolved endpoints identified by the
[saved recorder-pair audit](../ilvis0-shared-leg-diagnosis-20261014/README.md), plus
the corresponding model/processing endpoint of each successful neighboring recorder.
Each recorder retains its own original whole stretch. Raw recorder differences
remain measured on common UTC seconds; a neighboring fit never replaces a failed fit.

There are **six diagnostic identities, ten native evaluations per identity, sixty
maximum overall, zero optimizer starts and no retries**. Each identity evaluates
the saved center twice with the value implementation and twice with the automatic
derivative implementation. It then evaluates both implementations at full, half
and quarter of the same bounded local affine correction. The affine calculation
uses the existing bounds and a maximum of 100 local linear iterations; it is not
a refit of the observed recording.

The diagnostic records central reproducibility, agreement with the saved objective,
value-versus-tangent coordinate differences, actual versus affine-predicted cost
changes, endpoint stationarity and actual physical prediction changes. It does not
weaken a tolerance, change physical assumptions, or promote any scientific result.

The frozen selector, six source hashes, endpoint values, numerical source snapshots
and environment are recorded before native evaluations. Original extraction must
reproduce the saved provenance. The nominal 200 Hz interval, covariance, calibration
bounds and processing assumption remain those used in the completed recovery.

Each call is charged durably before execution. Exclusive locking prevents duplicate
workers. A charged interrupted identity is recorded as interrupted, without retry;
only unstarted identities may continue under unchanged hashes and environment.
Completed work cannot resume. Four numerical threads are the total allocation.

The results guide numerical qualification or a separate paired comparison; this
diagnostic makes no calibrated shape or background-field decision. Group-1 navigation
remains decoder/motion context, never an input to the Earth-model observations.

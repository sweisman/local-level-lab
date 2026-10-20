# Compare receiver-derived motion on development recording 187

Use the same 2,048 fixed row indices as the completed velocity diagnostic.
Do not replace unsupported centers or choose windows from their new results.
Read only the single GNSS-only PPP export for development recording 187; verify
its saved hash and preserve the original zero-eligible inventory.

At each supported closed ten-second window, assess the position-derived cubic
trend with the qualified method. Preserve full position covariance, actual times,
longitude representation and export rounding. Compare independence, an explicitly
supplied half-second correlation of 0.8, and arbitrary temporal correlation.
The supplied correlation is a sensitivity case, not a measured property.

Compare its course rate, north/east velocity and vertical motion with the saved
velocity diagnostic and reported velocities. Save residual RMS and lag-one
correlation by axis using a separate cubic least-squares calculation. Agreement
between these receiver quantities is a consistency check, not independent error
calibration. Missing instantaneous-motion bounds remain missing.

Finite proposal: one identity, one receiver file, at most 100,000 epochs, 2,048
charged windows, 2,048 position assessments, 2,048 residual fits and 2,048 point
kinematic conversions. One worker uses four numerical threads. The cooperative
wall allowance is 300 seconds; no retries, raw-IMU reads, native predictions,
model fits or protected confirmation reads. Freeze sources, environment, source
hash, center list and prerequisites before launch. This proposal spends no
allowance from the completed software study.

Publish every supported, unsupported and ambiguous window. Counts whose trend
interval lies within the old motion threshold are descriptive only: they create
no eligible flight, revised selection rule, instantaneous-motion guarantee or
scientific model decision.

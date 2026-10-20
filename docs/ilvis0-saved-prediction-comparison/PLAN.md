# Saved prediction comparison

Audit the two completed retrospective prediction studies using their published
fit ledgers and saved epoch errors only. No original extraction, integration,
optimization, parameter adjustment, covariance selection or retry is permitted.

The studies reuse one IMU21 recording, one receiver split and one conservative
flight group. The first has six fits; the correlation comparison has twelve.
They are **18 analyses of the same observations**, not 18 replications. Preserve
all original stopping labels, including three unresolved fits. Do not replace
them with the later whole-record convergence labels.

Verify SHA-256 receipts before reading each ledger and compressed epoch file.
Require the common 292-epoch training / 147-epoch prediction grid. Recalculate
direct north/east/up and horizontal RMS, endpoints and fixed 30-second sections;
compare recalculated RMS with the published ledgers. Use raw direct errors,
separately from covariance-conditioned innovations. Preserve absolute UTC and
source metadata and make every comparison traceable to its original artifact.

Report the three original fitting/error assumptions side by side. A complete
three-model set and an unfinished set must remain distinguishable. Do not
manufacture a new winner from horizontal RMS, tune an adequacy threshold to these
errors, compute a detection significance, or count error sections as new trials.

The finite metadata scope is two studies, 18 fit records and at most 10,000
saved epochs, one worker/four-thread ceiling, zero native calls or optimizer
starts. Freeze source/input hashes before the reductions. Plotting and publication
must use the saved audit, never trigger a prediction or fit.

This is retrospective development evidence. It clarifies what the existing
predictions show while global uncertainty, calibrated absolute adequacy and
independent-flight confirmation remain unresolved.

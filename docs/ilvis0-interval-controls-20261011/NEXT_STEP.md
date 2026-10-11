# Next integration check

Preserve the completed controls and original NASA findings. A finer synthetic sample
interval is a diagnostic; it does not supply missing information between actual
logged samples and is not a reason to upsample the archive.

The practical next question is whether an independently derived integration method
can recover the known motion and calibration from the original 200 Hz increments.
Test corrections for rotation changing within an interval (coning) and the interaction
of rotation with velocity increments (sculling), separately and together. Include
independently generated constant-rate, single-axis and changing-axis controls, with
matching continuous-reference integrals. Zero corrections must reproduce the old
method. Preserve gyro/accelerometer axis, mounting, calibration and timing conventions.

Use a separately versioned candidate and explicit finite software allowance. Compare
known-parameter prediction error, fitted calibration, objective and conditioning
equally under all three model identities. Recovering positions alone is insufficient.
Check angular and velocity increment conventions independently; distinguish ordinary
rate integrals from already compensated finite-rotation/velocity increments.

Do not apply a correction twice if an input stream already includes it. Unknown NASA
processing is a reason to preserve clearly labeled alternatives, not to choose the
one with the desired Earth-model outcome. An improved synthetic method is not
automatically the correct instrument model. No observed fit or corpus rerun is
authorized by this note.

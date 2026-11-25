# Compare averaged force directions on common RF04 timestamps

Reuse the same 383 candidate time windows and both GPS reconstructions
from the completed RF04 force-direction check. Center quarter-second
and one-second windows on whole RF04 seconds. For each width, keep a
center only if both packet clocks provide full packets covering at least
95% of that window and both GPS paths support the integration. Keep the
earlier and later split fixed. Compare the two clocks on exactly the
same centers. Report their actual interval-edge differences.

Sum the measured force increments in the instrument frame. Average each
candidate's required force over the actual whole-packet support using the
existing eight-node rule and saved quartic GPS trajectory. Express the
average in local axes at the center, then rotate it into the aircraft
frame using the RF04 attitude at that same second. Use the same
earlier-only constant mounting alignment and later metrics as the
single-packet check. Report all matched models, clock and GPS settings,
including prediction separations before and after alignment.

The reported attitude is held at the center of the window. It supplies
no measurement of movement inside the window. Summing body-frame
increments and using a midpoint attitude leaves unmeasured rotation as
part of the diagnostic error. The result cannot certify an absolute
gyroscope, force or receiver error limit, and it is separate from the
acceleration-only shape comparison.

Use one task and one numerical thread with 81 charged calculations,
up to 98,048 force quadrature evaluations, and a 120-second cooperative
cap. Bind the original force and RF04 receipts and the qualified recovery
files. Use no original IMU decodes, new Earth-model fits, or reserved ESA
reads. [Single-packet comparison](RF04_FORCE_DIRECTION_RESULT.md)

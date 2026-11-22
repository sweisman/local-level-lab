# Align the two added NASA recordings for withheld forecasts

Use the [two completed GPS reconstructions](GPS_RECONSTRUCTION_EXTENSION_RESULT.md)
and the original, independently selected inertial windows. Join receiver
reports by exact millisecond tag after the saved GPS-to-UTC adjustment.
The original IMU8 window has 585 reports and one additional reconstructed
epoch outside the window. The IMU21 window has 538 reports. Require both
GPS solutions at every original report. Use the first two-thirds of each
original window, rounded down, for training. Keep later positions in a
separate artifact. Keep later inertial packets and query times available
for the forecasts.

Use the same packet, physical conversion, installation and timing checks as
the first [input preparation](MATCHED_OBSERVED_INPUTS_RESULT.md). Preserve
original packet offsets and six signed counts. Test nominal and recorded
elapsed clocks with the existing ±0.15-second offset margin. Require the
original source hash, and reject missing packets or missing timing support.
Record the outcome for both windows with no adjustment to their boundaries.

Freeze both compressed originals with their existing source identities so
the packet selection can be reproduced. Use a maximum of 10 MB compressed
and 300 MB decoded per original, 150,000 selected packets per recording,
one charged decode per recording, two one-thread workers and a five-minute
wall limit. Permit one technical restart per unfinished task and at most
two interruptions under a separately charged ten-minute recovery stage.
The shared recovery qualification and arithmetic environment must match.
There are no new GPS position solves or inertial model fits in this step.

# Check withheld prediction accuracy across twelve receiver paths

Use the two complete settings and all six archived forecasts from the ESA
400/120 development comparison. Reuse the original training and later
times and raw forecast coordinates. Score the original processed receiver
positions, all seven saved code-only alternatives and four carrier paths
from GPS, GLONASS and the two Galileo receivers. None of these alternatives
changes the original training fit or the fixed position-accuracy limits.

Apply the original horizontal, vertical and peak error screen to every
forecast using the same 120 later times. Keep unadjusted metre errors
separate from the profiled shape score used in earlier audits. Compare
the globe family with the disc first using total 3D error, then compare
the two globe models where appropriate. Report the preferred forecast's
absolute error margins, plus the minimum additional arbitrary path
disturbance in 3D RMS needed to break each position limit. Distinguish the
original and carrier paths from lower-accuracy code-only stress paths.

One thread and a 60-second cooperative limit cover twelve frozen receiver
tasks, with six forecast evaluations per task. Preserve all source and
results manifests, observed screen failures and every numerical ranking.
The paths share an antenna and some inputs. Passing the screen on them is
a sensitivity result on the opened development window. Absolute position
truth, flight-to-flight coverage and the full calibration range remain open.

# Test separate innovation scales for the ESA forecast coordinates

Use the eight frozen windows on ESA development flight 187 from the
[motion-scale check](ESA_MOTION_INNOVATION_SCALE_RESULT.md). Keep both
published inertial measurement error laws, all later GPS positions and all
forecast means. Use the original native whitening factor and both unchanged
added covariance roots. The three slots are the ordered north, east and
height innovations of that factor. They are statistical coordinates of this
factor rather than measurements of separate physical error sources.

Compare the original covariance and the earlier shared motion scale with two
alternatives. The first gives each innovation slot its own quiet scale and
uses one common motion scale. The second gives each slot both scales. Use the
existing 15-second motion response. For each of the eight folds, load only the
other three turn-and-steady pairs to select the scales. Start from that fold's
archived shared scales. Run three deterministic sweeps through the separate
log scales on the integer grid from −5 to 5, keeping the smallest training
negative log score, with ties favoring the smaller log scale. Score the
omitted pair only after selecting both alternatives.

Verify the new score against a dense correlated covariance. Verify that the
shared-scale case reproduces the original result and that selection starts
from the fold's donor-only scales. Keep the existing joint error reference.
For this development check to clear it, require both better total held-out
log score than the shared motion scale and all eight windows inside the
reference under each error law. The same flight supplied earlier diagnostics,
so a pass could justify a separate qualification and cannot establish
independent-flight coverage or alter any shape result.

Freeze eight folds, two workers with one thread apiece, 330 candidate settings
per fold, and a 240-second cooperative limit. Bind the existing tested
recovery policy and a separate 360-second recovery limit. Use saved means and
covariance components only. No new trajectory fits or reserved flight groups
are permitted.

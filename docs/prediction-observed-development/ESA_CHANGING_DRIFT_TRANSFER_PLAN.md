# Test the changing-drift range on saved ESA forecasts

Use all 24 starts from the sealed 400/120 model comparison on ESA development
recording 187. Reuse every passing forecast and keep failed starts visible.
The earlier 400 receiver positions and the original forecast times are the
only receiver inputs to range construction. Use a common local coordinate
scale fixed at the first earlier receiver report. Save the full range and its
input hashes before opening any later receiver position.

Carry the 15-state changing-drift law, fixed process scales and 4.2 threshold
from the generated study into this development check. Run two white-receiver
cases. The first keeps the generated 3 cm per-axis standard deviation. The
second uses the reported full covariance at each earlier epoch and holds the
last earlier matrix fixed throughout the forecast. The changing position error,
receiver random walk and initial receiver offset are identical in both cases.
The operator starts at the first earlier epoch. It omits fitted calibration
uncertainty. These settings are sensitivity assumptions for a longer fitted
history and do not inherit coverage from the shorter known-truth simulation.

Score the first 60 and all 120 later positions. Retain raw and corrected RMS
and the original descriptive accuracy limits. Report whether every observed
coordinate falls inside the range, its widths and maximum normalized error.
For each complete three-model setting, use starts chosen by the existing
earlier training-cost rule. Report how many epochs permit separation of the
coordinate ranges between each shape pair, then within globe. These are
descriptive comparisons of ranges, with no significance or coverage claim.

Freeze both parent completions, generated policy and audit, exact earlier
inputs, sealed forecast hashes, source and environment. Limit the study to
two covariance operators over 520 reports and 48 condition-and-score cases on
one numerical thread. No navigation starts, native calls, new receiver
solutions or protected-group access are allowed.

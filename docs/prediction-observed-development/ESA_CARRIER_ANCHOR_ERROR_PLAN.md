# How accurate must the ground anchors be?

Extend the fixed two-minute carrier bound on the open ESA flight to allow
errors at the four permanent Nuuk anchors and both carrier endpoints. Use the
saved signed carrier weights and linearized range model. Recalculate only the
ten pairs adjacent to the six anchors. The earlier motion limit remains an
illustration. Leave the true carrier and position errors unknown.

Use the transpose of the range operator to subtract the score already accounted
for by the signed ranges. Bound the anchor contribution both when each position
can err independently inside the same per-axis limits and when all six errors
are a single common offset. Bound the remaining free-site contribution using
the saved residual weight norm and piecewise linear anchor interpolation. Show
per-axis position tolerances at carrier error caps of 0, 0.5, 1 and 1.5 mm RMS.
These are accuracy requirements in the fixed geometry, with no new claim about
the precision of the aircraft or ground measurements.

One task, one thread and a 180-second cooperative cap. Charge one setup, ten
pair calculations and one score bound on the 241-epoch grid. Reuse checked
task-level recovery. Run no new fits and read no reserved-flight measurements.

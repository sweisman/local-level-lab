# Compare both force instruments with measured airport gravity

Use the two original receiver-selected ground stops on the opened ESA
flight and the accompanying sealed iMAR force averages. Compare the
reported parking position of each stop with the matching apron
measurement in Table 2. Use the nearest named apron reference if it
lies within 100 m horizontally. This links the reference to the stop.
It does not establish the gravity difference across the apron.
[Campaign paper, Table 2](https://essd.copernicus.org/articles/17/1667/2025/#section3.3)

Use the exact time span covered by iMAR on each stop. For every
GIRAFE source file that overlaps it, keep all timestamps inside
that span and report the files separately. Overlapping exports
remain separate checks. Use the magnitude of the mean force vector
as the primary comparison with the existing iMAR baseline. Also
report the mean of instantaneous magnitudes, the atom channel on
its own and complete-minute variation. The original time-indexed
measurements remain unchanged.

Convert the published apron gravity magnitude from mGal to m/s².
Report the comparison with and without a working local height
correction of −3.086 micrometres per second squared per metre.
For that correction use the recorded receiver height minus the
published vertical antenna offset of 1.60 m for iMAR or 1.12 m
for GIRAFE. A ground stop does not quantify residual motion,
local gravity gradients or the accuracy of the transform.

Freeze two tasks, one per stop, using verified saved receiver and
iMAR results and the original GIRAFE acceleration files. Allow
two file reads and at most 321,325 GIRAFE rows per stop. Use one
thread and a 90-second ceiling. Keep the two reference values, the
source hashes and the exact time and matching rules in the freeze.
No iMAR reread, airborne fit, reserved flight or model decision.

# The left-side failures

Both preserved endpoints fail in the same way: the left branch reaches an unchecked neighboring packet boundary. Its cost and position changes pass the existing stability limits, but its aggregate stationarity check remains above the limit. The continuation guard therefore stops before checking both sides of that neighbor. The right branch passes.

| Source | Left stationarity | Limit | Cost change | Neighbor spacing (ps) |
|---|---:|---:|---:|---:|
| completed_primary | 0.000128666056 | 0.0001 | 1.63347e-11 | 0.259343 |
| verified_profile_companion | 0.000128666064 | 0.0001 | 1.75893e-11 | 0.259343 |

The saved branch reports contain aggregate gradient measures, so they do not establish which coordinate dominates every fresh left-side probe. They do establish that the current boundary has not passed its final stopping test. These failures must not be relabeled.

The existing complete-cluster search can instead look for a negative-to-positive timing slope change across the nearby packet boundaries, then apply the unchanged final two-sided gate at the selected knot. This avoids relaxing stationarity to cross an unchecked neighbor. Any observed test requires a separate finite freeze, source-to-final movement checks and both source endpoints.

This audit checked two saved target reports and their sealed publication receipt. It made zero native calls, read no original measurements, performed no fits and changed no labels. Findings remain 49 globe / zero flat / four unresolved.

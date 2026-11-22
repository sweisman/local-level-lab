# Compare both ground receivers using one aircraft path

Reuse the ten earlier and three later 30-second intervals, satellite lists
and signed aircraft and Qaqortoq ranges in the [same-cadence receipt](esa-ground-cadence-comparison-v1.json).
Read only the stationary Nuuk excerpt and the archived broadcast navigation,
final orbit and final clock products used for Qaqortoq. Verify their hashes
against the completed earlier studies. Recompute the expected Nuuk range
changes using those products, the same atmosphere calculation and the Nuuk
marker and antenna coordinates from the ground file.

Use the original validated two-frequency phase arcs. Omit a satellite when
the final products do not support both Nuuk endpoints. Recenter all range
vectors over the surviving satellites. An interval needs at least five
satellites. Use exactly the same saved aircraft residual for both ground
comparisons. Hold the earlier correction multiplier fixed on the three
later intervals, and report how the change in Nuuk satellite products moved
the ground residuals. This comparison still leaves common atmospheric,
tracking and aircraft position errors open.

One task and one numerical thread. Allow one setup and thirteen interval
checks with at most 22 satellite endpoints each. Use a 90-second cooperative
wall limit and the repository's qualified recovery. No aircraft model fit,
position reconstruction or reserved flight read is permitted.

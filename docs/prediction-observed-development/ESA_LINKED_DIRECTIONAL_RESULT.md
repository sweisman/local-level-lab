# Linking the calibration terms leaves the overall ESA forecast bound unchanged

The calculation checked all nine surviving calibration ranges on ESA
development recording 187. It collected the acceleration and force
terms that share a matrix before bounding their combined effect. All
36 planned bounds completed. Four ranges tightened relative to the
original subdivided cover, and none could be ruled out using the
earlier GPS positions.

| Candidate | Ranges checked | Tighter than the original cover | Best combined-cover bound |
| --- | ---: | ---: | ---: |
| Zero-field globe | 4 | 3 | 20.65 |
| Zero-field disc | 5 | 1 | 33.01 |

At zero assumed earlier unshared error, the best combined upper bound
remains **53.66 units**, above the **25.41-unit** forecast difference.
The largest bound is still in disc range 2/3. The 37 saved linked-point
memberships in these ranges all remained consistent with the new
checks. This leaves the forecast comparison inconclusive over the full
calibration range. The study starts no new fits and reads no later GPS
positions or reserved flight data.

Fourteen software checks passed before the run. A known-answer case
showed that the new bound preserves cancellation between two calibration
terms driven by the same matrix. The recorded calculation used the
existing allowance for numerical error in the static map. Error in the
full integrating model still needs its own bound.

[Frozen plan](ESA_LINKED_DIRECTIONAL_PLAN.md) ·
[All range bounds](esa-linked-directional.json) ·
[Sealed evidence bundle](esa-linked-directional-evidence/replay.zip)

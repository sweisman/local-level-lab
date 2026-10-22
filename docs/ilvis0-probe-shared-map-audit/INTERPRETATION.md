# Calibration cross-effects explain most of the sampled mismatch

Adding the 24 shared calibration terms improves agreement for **all twelve
fixed probes**. These terms retain effects such as a calibration offset acting
through an uncertain orientation; the simpler linear diagnostic omitted them.

| Processing case | Largest linear-only mismatch | After shared terms |
|---|---:|---:|
| Zero removal | 845 m | 48 m |
| Profiled removal | 3,955 m | 216 m |

This explains much of why the simplified linear formula admitted calibrations
that the full model rejected. The remaining mismatch is still material. The
next audit will use the already saved derivatives at each probe to examine
that remaining curvature and identify which parameter combinations matter.

These are comparisons at generated points, not aircraft errors or confidence
intervals. No earlier training-conditioned error bound was applied to a point
outside its stated region. Nothing here proves coverage of unexamined
calibrations or changes the original 53-stretch findings.

[Verified calculation](README.md) · [Next saved-data audit](NEXT_PLAN.md) · [Current work](../NEXT_STEPS.md)

# Use tangents to the original loss ball to propose tighter score bounds

Use the eleven surviving children and exact previous bounds from the
[scaled calibration search](ESA_LINKED_SCALED_PROPOSALS_RESULT.md).
The scaled solver converged on two score searches, while the bound
covering the complete calibration range stayed at 53.20 units.

Keep the same ranges, score, earlier squared-loss increase of 0.01,
zero unshared error and static-map allowance. In the normalized proposal
coordinates, replace the direct score search with the existing bounded
linear-programming method that adds tangents to the earlier residual norm
ball. Start from the archived earlier-loss direction and allow at most
16 tangent iterations per child. Combine the tangent multipliers into
one earlier-loss direction. Verify the new score certificate in the
original linked physical coordinates. Check every saved feasible witness.
Retain the existing bound if the candidate certificate is unavailable or
weaker. Earlier exclusions and every unchanged box remain in the cover.

Verify the tangent method on a generated problem with a known support
value before using the saved child ranges. Use eleven identities and at
most 22 charged proposal or certificate checks, two one-thread workers
and a 120-second cooperative deadline. Each task may solve at most
16 linear programs and evaluate one score certificate. Use zero new
trajectory fits, integration, later GPS reads or reserved-flight reads.
Report the verified combined bound against the original 25.41-unit gap.
The result applies to the static map under the same assumptions.

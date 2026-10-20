# The method admits impossible extreme examples

All 36 tested extreme matrices fail the rotation-invariant check. All six known
physical anchors pass. The largest defects are about 0.74–0.87, far above the
declared dimensionless numerical allowance of 0.00000001.

After removing the proposed sensor gains, a physical matrix must preserve the
original matrix's rotation invariant. The saved extreme examples do not. They
are feasible in the simplified prediction region, but fail this necessary
physical condition. This explains one source of unnecessary freedom in the
current uncertainty calculation.

It does not show that every wide prediction is impossible, or prove what the
correct narrower range should be. New constraints must preserve all permitted
physical calibrations before any interval can be tightened.

The next derivation will use the allowed orientation range when bounding each
matrix column. The existing constraints allow any rotation, losing information
about how far orientation can depart from its declared center.

The nine local known-answer checks pass, including nonorthogonal initial
matrices, gain removal, stretched and nonorthogonal columns, and the fact that
a Gram check alone cannot establish a proper rotation. The frozen diagnostic
completed all 42 checks in 0.6 seconds with no LP proposals, integrations or
original aircraft reads. The 53-stretch findings remain unchanged.

[Results](README.md) · [Next derivation](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

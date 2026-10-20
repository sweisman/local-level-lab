# Joint constraints sharply narrow acceleration

All six generated cases passed independent exact support checks. Their projected
acceleration-change radii are 0.467–0.506 m/s², compared with the earlier full-box
radius of 6.6685 m/s²: a reduction of about 92–93% in every group.

The improvement comes from retaining relationships between calibration terms.
Their individual allowed ranges remain wide, but the combination that determines
acceleration is much better constrained by training observations. No known
simulated calibration or later observation constructed these bounds.

The six cases completed in 2.9 seconds, within the frozen 36 LP / 108 exact
support allowance. All 51 coordinates and original physical bounds remain.
Known anchors were opened only after saving the bounds, and all stayed feasible
and contained. There were no aircraft reads, fits or native integrations.

This passes the acceleration engineering target, not the full prediction target.
The next test must carry the verified change bounds into propagation while
preserving the original expansion, shared coefficients and unqualified remainder
allowances. It must reject certificates belonging to another source or training
region. The 53-stretch findings remain unchanged.

[Complete results](README.md) · [Next qualification](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

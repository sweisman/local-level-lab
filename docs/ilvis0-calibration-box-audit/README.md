# Calibration-box audit: input checks stopped execution

All six cases were rejected before any numerical projection. The wrapper compared the training region with the identity of an older shared-coordinate subset, rather than its full reference identity. No trajectory calculation or model fit ran. The six charged starts and their failures remain preserved.

A separately frozen [corrected audit](../ilvis0-calibration-box-audit-v2/README.md) addresses the same question with the correct reference check. This failed wrapper adds no scientific evidence.

[Original scope](PLAN.md) · [Prediction roadmap](../ANALYSIS_ROADMAP.md).

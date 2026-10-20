# The value constraint helps on the actual baseline

All six controls using generated source data pass. Their geometric vertical ranges retain
about **5.6–6.3%** of the original body-rotation interval width. The calculation
keeps the existing training-derived force range, and the independent known
points remain inside the reported intervals. It completed in 3.45 seconds.

This addresses the baseline mistake in the previous trial: the comparison now
uses the actual saved source, body prefix and learned force information. The
literal installation matrix is left unchanged; its small metric defect is
bounded explicitly.

These are generated-source component controls, not new aircraft results. The
range covers force values. It does not yet bound error from the native reference
linear map. Matching those coefficients—or accounting for their differences—is
required before replacing a propagation remainder. A narrower value interval
alone does not qualify a complete position prediction.

[Complete evidence](README.md) · [Next step](NEXT_PLAN.md) ·
[Previous baseline diagnosis](../ilvis0-directional-prediction/BASELINE_DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

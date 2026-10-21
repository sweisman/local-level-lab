# Source derivative checks pass

All **10 known-answer controls pass**. They check rotation values and
derivatives against independent exact-rational calculations, source calibration
signs, both sides of a packet-clock boundary, and a mean-value error bound with
an explicitly displaced numerical center and row.

The stream retains all 27 physical parameter columns and uses 43,912 bytes of
working state. The study charged 26 bounds and 85 logical steps, reserved five
initializations and 41 rational references, and used no aircraft observations
or complete trajectory evaluations.

The next gate connects these derivative bounds to the existing physical and
training constraints, then checks the complete native calculation. These
component checks alone do not qualify full-recording widths or observational
confidence. The earlier nine-pass study and its unexecuted mean-value check
remain preserved separately.

[Results](README.md) · [Frozen scope](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

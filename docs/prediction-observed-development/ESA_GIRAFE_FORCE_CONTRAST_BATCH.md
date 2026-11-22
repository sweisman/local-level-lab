# Finish the turning windows with batched force calculation

The scalar run reached its three-minute cooperative time cap. Four
straight-course windows passed. The first turning window stopped at
the cap after 442 charged averages. Three turning windows never
started. All task receipts and charges from that run remain sealed.

The batched calculation keeps the receiver rows, geometry equations,
gravity assumptions, quadrature, offset rule and scores. It evaluates
the quadrature points together. Tests compare every model, gravity
assumption and averaging width with the scalar calculation.

Run only the four turning windows in v3, with the exact input files from
v2. Allow one numerical thread, 3,072 force averages, 208,896 quadrature
points and 90 seconds. Preserve the original interrupted result and its
charges. Use the four passing straight-course records directly in the
combined report. No additional model calibration or reserved flight.
[Original design](ESA_GIRAFE_FORCE_CONTRAST_PLAN.md) ·
[First accounting failure](ESA_GIRAFE_FORCE_CONTRAST_ACCOUNTING.md)

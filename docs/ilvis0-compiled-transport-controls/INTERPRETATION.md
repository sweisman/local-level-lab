# The compiled calculation passes the native controls

All **24/24 generated controls passed**. The study charged 78 native evaluations,
348 bounds and 15,072 two-pass bound steps, completing in 98.36 seconds with four
single-thread workers. Every result records the frozen arithmetic source hash.

The original reference, derivative, stationary-pose and nonlinear-containment
limits were retained. The calculation preserves reference centers, training
constraints and all 27 physical plus 24 shared-error columns. Separate local
checks compare primitive bounds with exact arithmetic and reject unsupported
rounding or subnormal modes.

This qualifies the component on the declared generated controls. It does not
prove useful error ranges over a whole recording, certify every floating-point
operation in the solver or establish statistical coverage. The tighter
norm-constrained body-source interval is not installed. No aircraft data was
fitted and no protected ESA record was used.

[Result and evidence](README.md) · [Fixed scope](PLAN.md) ·
[Next check](NEXT_PLAN.md).

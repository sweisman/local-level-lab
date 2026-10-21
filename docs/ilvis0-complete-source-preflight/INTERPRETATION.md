# All source domains are supported

All **48 declared regions pass**. Each safely inherits its parent's training
constraints and acceleration bounds, and each passes the initial-source
nonlinear-cap check. No calibration cap or error allowance was enlarged.

The study verified 288 parent support certificates and performed 48 source-cap
calculations in 17.48 seconds with four single-thread workers. There were no
trajectory predictions, optimizer starts or aircraft-data reads.

The remaining setup gate is a complete known-answer training/prediction check
of the joint adapter. After that, a separately frozen comparison can test the
full prediction ranges across all models, processing cases and mounting regions.
The complete width target remains four of six groups; the aircraft findings
remain unchanged.

[Results](README.md) · [Frozen scope](PLAN.md) ·
[Next-method requirements](../ilvis0-taylor-range-preflight/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

# The complete calibration relationship passes its component checks

All 24 source/domain identities passed. The calculation retains all 27 physical
calibration values and all 24 derived errors. It encloses their relationship
instead of letting those errors vary independently.

The checks cover full, narrow, fixed and gain-boundary domains for all six
generated candidate/processing groups. They compare 1,158 source evaluations and
1,158 separate analytic Jacobians, preserving all 27 derivatives per component.
All 1,611,936 reserved scalar inequalities reconcile with the checked results.
The run took 20.6 seconds.

The value allowance is 3e-10 in normalized error units. Independent derivative
comparisons use a 3e-8 tolerance; that tolerance does not enlarge the exported
coupling rows or supply their gradient bounds. Analytic tails and interval
differentiation supply the mathematical construction. These are numerical
assumptions, not measured IMU accuracy or a whole-program roundoff certificate.

This addresses the representation problem found by the extreme-point diagnostic.
Whether it makes prediction ranges useful is still untested. No native trajectory,
aircraft observation, model fit or scientific decision was produced here.

[Results and accounting](README.md) · [Frozen scope](PLAN.md) ·
[Next prediction comparison](NEXT_PLAN.md).

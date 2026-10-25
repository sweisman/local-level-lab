# Draw new noise without changing its covariance

All 30 checks pass. Both formats retain bitwise-identical original-seed
arrays, bindings and charges compared with the frozen earlier generator.
New seeds change the sensor and receiver errors while preserving the covariance
law, draw budgets and earlier-prefix behavior. Invalid seeds and changed noise
parameters are rejected. No fitting or archive measurements are used.

This qualifies the draw interface, not prediction coverage or a model decision.
The next finite full-pipeline pilot has its own qualification and allowance.

[Draw plan](../INDEPENDENT_DRAWS.md) · [Pipeline pilot](../PIPELINE_PILOT.md).

# Conservative training-box qualification

Qualify the already tested affine contractor before it is connected to native
prediction bounds. This study uses generated inequalities only: no archive,
Earth-model fit, native integration or protected ESA evaluation.

Freeze 24 identities: four signed known intervals, four known contradictions,
four deliberately uninformative systems and twelve coupled 27-column systems.
For the coupled systems, independently evaluate 64 exactly representable feasible
points with rational arithmetic and require all of them to survive contraction.
Seven zero columns must retain their complete original ranges. No point is
discarded after inspecting the contracted answer.

The contractor uses outward arithmetic and at most eight passes. Known intervals
must enclose their exact solutions and agree with the expected endpoints within
1e-14. Known contradictions must be explicit; weak systems must remain unchanged.
Every result retains all 27 coordinates and a scientific abstention.

Finite limits: 24 contractions, at most 648 input rows, 1,536 exact-oracle points,
eight passes per contraction, four total numerical threads and 60 cooperative
wall seconds. Each start records and reserves its row/point/pass allowance before
evaluation. No retries, signals or reuse of unused completed allowance.

Passing verifies affine necessary-constraint propagation. Measurement allowances,
global nonlinear remainders, training-only initialization and covariance
assumptions remain separate requirements. Weak valid input constraints may still
give no contraction. This study does not authorize narrowing a native region
without a valid bound over the entire box.

[Method and remaining requirements](../ilvis0-native-stream-interface/TRAINING_REGION_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

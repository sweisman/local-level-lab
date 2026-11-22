# Recorded-aircraft check for skipping exact duplicate solver evaluations

This numerical qualification tests the option that passed the [eight generated
fits](MATCHED_REUSE_GENERATED_RESULT.md). It uses two passing fits from the
[sealed preflight](MATCHED_OBSERVED_NUMERICAL_RESULT.md). The IMU8 reference
is the specified-field globe, a control with no rejected-only evaluations.
The IMU21 reference is the zero-field globe, which had the only rejected-only
evaluation among the six passing preflight fits. The cases cover two recorder
types and two rotation settings. The study does not run the earlier failed fit.

Keep the original normalized start, nominal 200 Hz clock, calibration limits,
motion data, receiver training prefix, wide arithmetic and stopping checks.
Check the frozen compilation against the original native source, compiler and
flags. Predict on the original query times, with receiver positions available
only during training. Both fits must pass their stopping checks and use at
most their original number of native training evaluations. The starting loss
must agree within relative `1e-12` or absolute `1e-10`. The final loss difference
divided by the largest of one and the two losses must be at most `1e-8` in
absolute value. The maximum forecast displacement on later query times must
be at most `0.01 m`. Record the observed saving, including zero if the selected
controls contain no duplicate proposals. The test does not estimate a typical
speedup on aircraft or change any scientific result.

The direct limits are one start and 30 training calls plus one forecast per
case, two single-thread workers and 20 minutes of elapsed time. Record source,
environment, inputs and task identities through the shared study runtime.
The qualified task-level recovery allows one technical restart per unfinished
task, at most two interruptions in total and 40 minutes for one recovery stage.
A scientific nonpass is sealed. There is no additional forecast or fit budget.

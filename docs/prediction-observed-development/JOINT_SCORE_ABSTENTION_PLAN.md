# Test a conservative whole-path decision rule

The development rankings used the smallest joint error even when all three
models fit poorly under a given law. This check adds an absolute standardized
error requirement and an explicit option to abstain. It leaves the earlier
numerical comparison as a separate study.

For each model and each of the four frozen error assumptions, compare its
conditional squared standardized error with the central 95% chi-square
reference for the number of later coordinates. This reference assumes a
correct fixed Gaussian forecast distribution. Fitting and error-law
misspecification can change its meaning. It is a software reference with
no aircraft calibration.

Keep a model compatible if at least one error assumption stays below the
upper reference limit. Scores below the lower limit can indicate a scale
mismatch and never exclude a competing model. If both shape families
remain compatible, abstain. If just one remains, require at least one
member to lie inside the reference band. For the ESA development audit,
require the same error assumption to pass the unchanged position-accuracy
screen. That screen can withhold a decision and cannot exclude a competitor.
Assess the field only after selecting globe and require a single compatible,
adequate globe variant. A numerical failure leaves the setting incomplete.

Apply the rule to the 12 earlier generated development histories and two
saved histories from a separate route study. Both latter histories use the
same noise seed and a specified-field globe. They test transfer across
motion. Independent error rates and the other two generating models require
fresh tests. Audit the four ESA development settings with the same rule.

Freeze the method, inputs, source and environment. Reuse prior scores where
available. Allow eight new covariance operators, 24 joint evaluations and
two original seeded GPS reconstructions for the route controls. Use one
thread, no new fits, new seeds or protected aircraft reads.

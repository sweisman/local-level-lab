# Compiled arithmetic for longer uncertainty calculations

The exact rational implementation remains the reference. A separate compiled
component now performs the same derivative operations with outward-rounded
binary64 intervals. Seven tests compare products, reciprocals, square roots and
trigonometric derivatives with the rational reference, including subnormal and
extreme-scale inputs. All pass.

The component checks its numerical environment and records source, compiler and
binary hashes. Unsupported inputs fail. It is not installed in any completed
or running study.

This qualifies individual arithmetic operations. It does not yet establish
whole-trajectory speed or accuracy, useful prediction ranges, native execution
error or an observational error model. The [compiled midpoint step](../ilvis0-path-step/README.md)
passes ten checks. Its [packet-loop connection](../ilvis0-compiled-path-packets/README.md)
also passes ten local checks; a separate finite native comparison covers longer
prefixes. Whole-history bounds remain a further requirement.

[Mathematics](MATHEMATICS.md) ·
[Native adapter comparison](../ilvis0-path-native-controls/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)

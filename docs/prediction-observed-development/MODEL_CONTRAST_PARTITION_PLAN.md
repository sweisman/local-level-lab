# Separate model contrast from shared forecast error

Partition the sealed whole-path errors into two components. One is in the
span of the differences among the three model forecasts. This is the
part that changes the model ranking. The other is perpendicular to those
differences and is the same for all three models. Work in the original
joint covariance metric for each of the four error assumptions.

Use all twelve saved matched generated cases with known answers and the
two complete settings on opened ESA recording 187. Recover the generated
forecast centers from the sealed earlier fits and verify their hashes.
The ESA comparison uses its sealed pair distances. Recover the partition
from these distances and the existing three squared errors. The retained
energies must reproduce the sealed scores and preserve the model order.
Keep incomplete ESA settings visible. The per-component energy and its
nominal dimension are diagnostics alongside the whole-path error.

Use one thread, 48 generated covariance operators, 144 generated pair
distances and 56 partitions. Read no later receiver observations, generate
no receiver noise, make no fits and open no reserved flights. This is a
development check of score structure before choosing or calibrating a
future test.

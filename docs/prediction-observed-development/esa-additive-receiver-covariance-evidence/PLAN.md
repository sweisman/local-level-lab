# Fit a shared forecast term alongside the receiver error terms

Direct covariance replacement failed in every window. Use the existing
covariance as a shape for the shared forecast term, with its magnitude
estimated anew. For each GPS solution, add its measured receiver term
in physical coordinates. This keeps the combined covariance positive
and leaves the forecast paths unchanged.

For each of the four omitted pairs and both input conventions, keep the
receiver terms fitted on the six donors. Estimate one multiplier on the
shared covariance, common to all three receivers, using those six windows.
Choose from 1/16, 1/8, 1/4, 1/2, 1, 2, 4 and 8. Minimize the summed
normalized Gaussian marginal scores. Prefer the smaller multiplier on
ties. This sum compares prediction accuracy for three GPS solutions that
share an antenna. It does not treat them as independent observations.

Save the choice before reading either omitted window. Compare the
alternate policy with the original fixed covariance on the same forecast
paths, receiver positions and matched times. Record both Gaussian scores
and Student reference outcomes with the previously selected degrees of
freedom. Count the test as a development improvement only if the summed
omitted Gaussian scores improve under both input conventions. Report every
receiver and window even if the overall test improves. The fitted shared
term may include common GPS errors and forecast errors. This one-flight
comparison cannot separate those contributions or open reserved flights.

Freeze the two earlier reports, exact fittable inputs, tests, code and
environment. Run eight pair tasks on two one-thread workers, zero new
trajectory fits, and at most 49 bound calls and 198 bound steps per
pair. Allow 180 seconds cooperatively, with separately charged recovery
at most once per unfinished task and a separate 180-second allowance.

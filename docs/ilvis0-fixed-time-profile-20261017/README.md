# Refit the two timing solutions

The saved comparison of the closest-to-complete unresolved stretch found two
time offsets about 45 ms apart. This study fits the remaining nuisance parameters
at each offset from both saved starting solutions. It asks whether each fixed
time gives a repeatable result, and how their costs compare.

The finite scope is four conditional profile fits and two fresh controls: six
identities, 330 native calls maximum, four total numerical threads and no retries.
The observations, calibration bounds, receiver weights and forward model stay
the same. The planned final diagnostic would retain the full timing derivative.

Passing a fixed-time profile does not establish a completed free-time fit or
change the globe/flat tally. The existing full comparison and repeat requirements
remain necessary. The worker publishes all results automatically on completion.

The [software qualification](../ilvis0-fixed-time-controls-20261017/README.md)
passed all 21 checks, including three compiled-motion controls. The study completed
six identities using 23 native calls. Both controls passed. All four profile fits
reached their conditional stopping checks, but an incompatible accounting label
blocked the final diagnostics before those calls were made. Their saved error
labels remain unchanged. The [separate endpoint verification](../ilvis0-profile-verification-20261017/README.md)
checks the saved solutions without repeating the fits.

[Finite plan](PLAN.md) · [Saved timing diagnosis](../ilvis0-timing-basins-20261017/INTERPRETATION.md) ·
[Current findings](../CURRENT_STATUS.md).

# Check whether one GPS satellite drives the carrier-phase comparison

Use the saved 1,038 half-second steps from ESA development flight 187. Keep
the same receiver anchor, clock-step correction, supported satellite sets,
ephemerides and atmospheric model. Use the saved position and clock solution
to evaluate one linearized range equation per supported GPS satellite. Apply
the atmospheric correction at the saved endpoint and record any mismatch
with the archived range RMS from the original atmospheric update.

For each step, separate the range residual into components parallel and
perpendicular to the position-and-clock design. Compute the linearized
change in position when each satellite is omitted using the least-squares
deletion identity. Retain every eligible deletion and any geometry failure.
When a satellite was not used, its deletion contributes zero at that step.
Sum the changes from the original anchor and apply the frozen 400/120 score
operator. Report the largest effect on the signed forecast score, the effect
of deleting each satellite, the missing supports and range-residual RMS.
Verify the deletion identity against independent explicit refits, including
a synthetic shared position-and-clock error that the residual cannot expose.

Charge each archived-geometry step before evaluation. Four contiguous
step blocks run on two one-thread workers within a 180-second cooperative
limit, with 1,038 step checks and at most 32 satellite rows per step. No new
navigation solution, inertial fit, forecast, reference path or reserved flight
enters the calculation. The deletion result is a local sensitivity test.
A coherent range error parallel to position or clock remains unobservable
from the satellite residuals alone.

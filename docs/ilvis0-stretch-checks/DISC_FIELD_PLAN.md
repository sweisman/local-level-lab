# Plan: give the disc the background field on every stretch

## Question

The published comparison fitted the globe with and without the specified
background rotation field. It fitted the flat disc without the field only.
Does the disc still fit worse than the globe when the disc is given the
same field?

An **IMU (inertial measurement unit)** is the aircraft instrument whose
gyroscopes and accelerometers supply the measurements.

## What is fitted

All 53 selected NASA stretches, with their saved intervals unchanged. Each
stretch gets two new fits of one candidate, the disc with the specified
field:

- with no previous field subtraction assumed;
- with a common fraction of the field allowed to have been removed.

Everything else matches the published fits: the same recorded IMU and GPS
data, GPS weights, starting values, parameter limits including the 1°/hour
gyro offset, solver, and limit of 200 evaluations per fit. The disc with the
field uses the disc's own distances and the field term of the model code.

That is 106 fits, one start each. A fit that stops without meeting the
stopping check keeps its result and is reported as unfinished. Nothing is
refitted to improve an outcome.

## How the result will be read

For each stretch and each of the two cases, the new disc cost is compared
with the better of the two published globe costs for the same case. The
report gives:

- how many stretches have a lower globe cost in both cases;
- the smallest ratio of disc cost to globe cost;
- how the field changed the disc's own cost;
- how many new fits met the stopping check, and which did not.

An unfinished fit gives an upper limit on that candidate's cost. A stretch
with an unfinished or failed disc fit is listed separately and does not
count as resolved. These are fitted preferences on recordings already used
in development. They carry no statistical significance and do not replace
confirmation on independent flights.

## Limits and recovery

One worker with one numerical thread, up to 201 model evaluations per fit,
and a 48-hour cooperative time limit. Every evaluation is charged before it
runs. Each stretch is one sealed task. If the computer restarts, finished
stretches are reused, an interrupted stretch stays charged, and the shared
task-recovery procedure may rerun only unfinished stretches under its own
finite limits. Before launch, one model evaluation at a published solution
must reproduce the published cost.

[Review finding S3](../red-team-20261125/README.md#s3-the-disc-was-rarely-given-the-background-field)

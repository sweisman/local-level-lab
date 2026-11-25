# Plan: allow larger gyro offsets

## Question

Every published fit of the 53 stretches let each gyro be off by a constant
amount of up to 1°/hour. On one straight, level leg, the turning a globe
predicts looks much like a constant gyro offset of several degrees per hour.
If the gyros are allowed offsets that large, does the disc catch up with the
globe?

An **IMU (inertial measurement unit)** is the aircraft instrument whose
gyroscopes and accelerometers supply the measurements.

## What is fitted

One stretch for each of the 27 flight dates among the 53 selected stretches:
the longest stretch recorded on that date. A tie goes to the stretch whose
identifier sorts first. This choice uses no fit result.

Each chosen stretch gets nine fits: three candidates at three gyro-offset
allowances of 3, 10 and 30°/hour per axis.

| Candidate | Why it is included |
| --- | --- |
| Globe with the specified field | The comparison at the same allowance. |
| Disc without the field | The published disc candidate. |
| Disc with the specified field | Differs from the globe only in shape, so it is the hardest case for the globe. |

From the GPS speeds, headings and latitudes of the 53 stretches, the
rotation that separates the globe with its field from the disc is 7 to
15°/hour on the two level axes and up to 29°/hour about the vertical. An
allowance of 30°/hour covers all of it.

All fits assume no previous field subtraction. The second published case
adds a constant rotation that a gyro offset this large can already supply
on a straight leg, so it is left out here. The zero-field globe is left out
too. Omitting it can only make the globe look worse in this comparison.

Everything else matches the published fits: recorded IMU and GPS data, GPS
weights, starting values, every other parameter limit, solver, and limit of
200 evaluations per fit. That is 243 fits, one start each. Unfinished fits
keep their results and are reported as unfinished.

## How the result will be read

For each stretch and allowance, the lower of the two disc costs is compared
with the globe cost at the same allowance. The report gives the smallest
ratio at each allowance and the number of fits that met the stopping check.

It also reports the gyro offsets each candidate asked for. A real instrument
offset stays fixed in the sensor. An offset standing in for the globe's
turning has to change with ground speed, heading and latitude. The report
compares the disc's fitted offsets with the values the globe's turning
predicts for each stretch, and shows the globe's own offsets alongside.

If the disc matches the globe's cost on single legs at a wide allowance,
that will be reported plainly. The shape evidence would then rest on the
pattern of offsets across legs. These are fitted preferences on recordings
already used in development. They carry no statistical significance.

## Limits and recovery

Two workers with one numerical thread each, up to 201 model evaluations per
fit, and a 60-hour cooperative time limit. Every evaluation is charged
before it runs. Each stretch is one sealed task. If the computer restarts,
finished stretches are reused, an interrupted stretch stays charged, and the
shared task-recovery procedure may rerun only unfinished stretches under its
own finite limits. Before launch, one model evaluation at a published
solution must reproduce the published cost.

[Review finding S1](../red-team-20261125/README.md#s1-only-one-gyro-offset-allowance-was-fitted)

# Plan: compare the aircraft's own record with the instrument on 32 stretches

## Question

The selected NASA stretches were chosen and described using the laser
instrument's own navigation unit. On one stretch, flight RF04 of 2011, a
separate record kept by the aircraft operator confirmed the path and the
turning that the instrument recorded. Does the same hold on the other
stretches that have such a record?

## Records

The National Center for Atmospheric Research (NCAR) publishes a one-second
record for each research flight of the aircraft: roll, pitch and heading
from the aircraft's navigation system, and position from a separate GPS
receiver. The files for the [2011](https://doi.org/10.5065/D6R49P35) and
[2015](https://doi.org/10.5065/D6H70D6N) campaigns were taken in
unchanged. [Intake summary](intake.json)

Thirty-two of the 53 selected stretches fall inside one of these flights,
and the record has every second of attitude and GPS on all 32. Nine
stretches of 25, 27 and 29 October 2015 have no record in the files
received. Twelve stretches come from other campaigns.

## What is compared

For each stretch, at the reported UTC seconds and with no time adjustment:

- **The two GPS tracks.** The distance between the instrument's GPS
  position and the aircraft record's position, split into the part along
  the direction of flight and the part across it. The along-track part
  divided by ground speed is reported as an apparent time lag. Height
  changes are compared after each record is referenced to its own first
  height.
- **Turning.** The change in aircraft orientation over 1, 5 and 10 seconds
  from the aircraft record, against the rotation accumulated over the same
  seconds by the gyroscopes of the instrument's IMU (inertial measurement
  unit). Both the recorded packet clock and a nominal 200 Hz clock are
  used, with the gyro windows unshifted, 80 ms earlier and 80 ms later.

These are the calculations of the [RF04 comparison](../ilvis0-measurement-contribution/RF04_MOTION_MATCH_PLAN.md),
and the RF04 stretch is included so the earlier figures can be checked.

## How the result will be read

Every stretch is reported, including any that cannot be compared and why.
No pass mark is set. The RF04 figures give the scale to compare against.

The comparison shows whether a second system saw the same path and the
same whole-second turning. It evaluates no Earth model and enters no fit.
A turn that reverses inside one second can be missed. A lag that repeats
on every flight would describe how the two systems label time. It would
not say which one is right.

## Limits and recovery

One worker with one numerical thread and a one-hour cooperative time
limit. Each stretch is one sealed task with a fixed number of charged
steps. Finished stretches are reused after a restart, and the shared
task-recovery procedure may rerun only unfinished stretches under its own
finite limits.

# Plan: repeat the selection without the navigation-status flag

## Question

A stretch entered the published selection only if the instrument's own
navigation computer reported full alignment at every sample. That computer
uses globe equations. All 53 selected stretches come from files where the
flag was set throughout. Did the flag keep out any stretch that meets every
other rule?

An [earlier screen](../ilvis0-alignment-ablation/COMPARISON.md) asked this
for ten-minute stretches on 29 files and recovered only stretches already
among the 53. This plan asks it under the published rule, on every file.

## What is scanned

All 232 retained original files, each bound to its saved fingerprint and
timing check. The published selection rule is applied with one change: the
alignment flag is no longer required. Everything else stays the same,
including four minutes or more of data, GPS ground speed of at least
700 km/hour at every sample, the roll, climb and turn-rate limits, the
ten-second margins and the checks on the raw IMU records. An **IMU
(inertial measurement unit)** is the aircraft instrument whose gyroscopes
and accelerometers supply the measurements.

No gyro residual is examined and no Earth model is evaluated.

## How the result will be read

Recovered intervals are matched to the published 53 by original file and
UTC start and end. The report gives how many published stretches are
reproduced, and the number, total minutes and dates of any additional
intervals.

An additional interval is a candidate only. The roll, climb and turn-rate
values come from the same navigation computer and may be less dependable
when its flag is not set. Before any candidate is fitted, a separate fixed
rule must check its motion from GPS alone and the information it carries
about every fitted parameter. The published 53-stretch study is unchanged.

## Limits and recovery

One worker with one numerical thread and a four-hour cooperative time
limit. Each file is one sealed task. Finished files are reused after a
restart, and the shared task-recovery procedure may rerun only unfinished
files under its own finite limits.

[Review finding S2](../red-team-20261125/README.md#s2-selection-depends-on-the-instruments-own-navigation-status)

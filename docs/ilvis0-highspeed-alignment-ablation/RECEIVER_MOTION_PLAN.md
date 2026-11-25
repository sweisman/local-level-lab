# Plan: check the 16 recovered intervals with GPS alone

## Question

[Repeating the selection](RESULT.md) without the navigation-status flag
recovered 16 intervals from a second recorder. Their roll, climb and
turn-rate checks came from a navigation solution that never reported
alignment. Seen through GPS positions alone, did the aircraft fly these
intervals as steadily as it flew the 53 published stretches?

## What is measured

For each of the 16 recovered intervals and each of the 53 published
stretches, the recorder's own GPS positions inside the interval are
profiled with the project's existing
[receiver-motion profile](../ilvis0-receiver-motion-profile/RESULT.md).
It fits straight lines to 30 seconds of GPS positions at a time and
reports ground speed, climb rate and how fast the direction of travel
changes. Gaps are not filled. No gyro, accelerometer or navigation-computer
value is used, and no Earth model is evaluated.

The 53 published stretches get the same calculation so that the recovered
intervals have something to be compared with.

## How the result will be read

The report gives, for the published and the recovered intervals
separately, the range of four measures: the 95th-percentile and the
largest climb rate, and the 95th-percentile and the largest rate of course
change. It also gives the lowest ground speed.

A recovered interval is counted as **inside the published range** when
none of its four measures is above the largest value among the 53
published stretches and its lowest speed is not below their lowest. Any
interval outside the range is listed with the measure that put it there.

This describes motion only. GPS shows the path of the antenna, not the
aircraft's roll or the direction its nose points. An interval inside the
range has not been accepted for fitting. That still needs a check of the
information it carries about every fitted parameter, and a fixed fitting
plan. The published 53-stretch study is unchanged.

## Limits and recovery

One worker with one numerical thread and a two-hour cooperative time
limit. Each interval is one sealed task. Finished intervals are reused
after a restart, and the shared task-recovery procedure may rerun only
unfinished intervals under its own finite limits.

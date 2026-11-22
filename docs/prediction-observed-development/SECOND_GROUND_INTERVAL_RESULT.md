# A second low-speed receiver interval

Applying the [same speed-only rule](SECOND_GROUND_INTERVAL_PLAN.md) to the
remaining reports in opened ESA development recording 187 found a second
run: receiver indices **45,253–48,942**, or **3,690 consecutive reports over
30.7 minutes**. It begins 5.2 hours after the first selected run and is at
approximately **64.13° N, 21.95° W**, compared with 64.19° N, 51.68° W for
the first. The aircraft is at a different location; its heading is not
established by a low-speed GPS track.

Median reported horizontal speed is 0.012 m/s and its 95th percentile is
0.027 m/s. Receiver position scatter around the run's median is 0.75 cm
north, 1.32 cm east and 1.35 cm in height. The ranges of one-minute position
means are 2.34, 2.57 and 5.21 cm, respectively. These are relative PPP
stability measures, not absolute position accuracy.

The [saved receiver-only result](second-ground-interval-result.json) binds the
selection, exact time/indices, original source hash and first-control hash.
Five focused selection tests passed. No IMU value, model fit or protected
flight was used to choose the interval. It can now serve as an independently
time-selected second raw-IMU baseline; any comparison must allow different
aircraft orientation and instrument behavior across the five-hour gap.

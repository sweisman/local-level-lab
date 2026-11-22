# A 65-minute ground receiver control

The [fixed speed-only rule](GROUND_RECEIVER_CONTROL_PLAN.md) selected the
longest low-speed run in the first window of opened ESA development recording
187: **7,815 consecutive PPP reports over 65.1 minutes**. Median reported
horizontal speed was 0.018 m/s; its 95th percentile was 0.051 m/s. Selection
used no position values, IMU measurements or model results.

| Relative receiver position | North | East | Height |
| --- | ---: | ---: | ---: |
| RMS around the run's median | 1.47 cm | 1.24 cm | 3.06 cm |
| Median reported position SD | 2.97 cm | 2.28 cm | 5.41 cm |
| Range of one-minute position means | 4.10 cm | 4.57 cm | 11.79 cm |
| Raw first-to-last displacement | −57.08 cm | −19.75 cm | −0.10 cm |

The small minute-mean range and much larger raw endpoint difference show why
a single endpoint is a poor summary of this interval. The fixed rule retains
that endpoint; this report does not discard or repair it. Its cause remains
unresolved. The 95th percentile absolute deviation from the median is about
2.1 cm north, 2.4 cm east and 5.9 cm in height.

This is useful **relative stability** evidence for the GNSS-only PPP receiver
stream on the ground. It does not prove that the true aircraft position is
known to centimetres: the aircraft might move slightly, position and
velocity share one PPP solution, and a common coordinate offset is invisible.
Airborne receiver errors and the IMU error law remain unqualified. No Earth
model was fitted or decided. The [saved result](ground-receiver-control-result.json)
records the exact selected indices, criteria, source hashes and complete
statistics. Six focused tests for the ground and full-record receiver audits
passed.

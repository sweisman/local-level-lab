# Receiver-visible motion control

The earlier generated vibration oscillates at 10 Hz while the receiver
reports at integer seconds. At every scored receiver time, its position
change is the same 0.2 mm north offset and its pitch change is zero. A
separate motion control must vary at the receiver times before it can
stress the withheld-position error law.

Keep the existing generator and its sealed studies unchanged. Add a
0.37 Hz analytic north displacement of amplitude 0.1 m and an analytic
pitch change of amplitude 0.001 rad, both of the form `A(1-cos(2πft))`.
This leaves position, velocity and attitude at the start unchanged.
Derive velocity, acceleration and pitch rate analytically; recompute
body gyro and specific force from the resulting motion. Use the existing
independent noise streams with identical seeds in the motion-on and
motion-off cases. Retain the baseline 10 Hz component in both cases so
the existing propagator's initial state remains exactly aligned.

Software qualification requires: changing receiver-time truth rather
than a constant offset; matched noise draws; finite-difference agreement
with analytic motion derivatives; and clean IMU propagation to the
analytic receiver path. This is a generated software control, not a model
of all aircraft maneuvers or an aircraft coverage result. Only after
qualification may a separately frozen finite paired pilot score the
fixed 15-state error law. No ESA reserved group or Earth-model fit is used.

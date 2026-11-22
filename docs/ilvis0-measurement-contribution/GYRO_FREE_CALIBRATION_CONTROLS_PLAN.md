# Qualify training-only gyro-free calibration on known forces

Fit one set of three accelerometer gains, three biases and a gravity
correction to earlier force magnitudes. Use the [packet calibration](GYRO_FREE_PACKET_CALIBRATION.md)
on measured increments and time quadrature on the required force. Use
the same whole-packet time support on both sides. Keep all seven fitted
parameters and apply the same positive-definite force covariance to all
training evaluations. Keep the later packets, target forces and scores
out of training and save the calibration before opening them.

Use eight generated force records. Four use the nominal clock and four
use variable elapsed intervals. The targets have an exactly integrable
vertical force. The sensor directions vary between packets, with each
recording sharing known gains and biases. Hold the earlier calibration
fixed on later packets. Require the original numerical stop and later
force RMS at most \(10^{-6}\) m/s². Require the same calibration to miss
an independently altered later force of 0.025 m/s² by at least 0.024
m/s² RMS. Check forecast agreement without requiring unique parameter
recovery. These controls test the software and the split.

Separately check a continuous-motion error bound against a rotating
force with a known exact packet average. If body-frame force changes
at no more than \(L\) m/s³ over a packet of length \(\Delta\), the
variance of the force vector within that packet is at most
\(L^2\Delta^2/12\). This follows by writing the variance as half the
mean squared difference between two times in the packet. If the packet
average vector has magnitude at least \(m\), the difference between
the continuous mean magnitude and the magnitude of the averaged vector
is bounded above by
\(\min(L\Delta/\sqrt{12},\,L^2\Delta^2/(24m))\). For \(m=0\), use the
first term. A recorded-data application would need independently
supported bounds for body-frame force change, including aircraft
turning. The generated tests do not establish those bounds.

Freeze two one-thread workers, eight single-start fits, 80 training
residual calls per case, the solver's matching derivative and endpoint
allowance, and two later checks per case. Charge work as it runs. Use
a three-minute wall cap with the existing qualified task recovery, at
most one technical restart per unfinished case, two interruptions total
and a three-minute recovery cap. Use no archived aircraft outcomes.

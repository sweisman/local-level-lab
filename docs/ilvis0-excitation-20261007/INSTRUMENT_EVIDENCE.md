# What supports an IMU6 assumption, and what still does not

This review concerns the six prepared **IMU6** recordings. They are separate from the
different IMU8 reference sample. Their decoded increments and good decoder-reference
agreement are useful evidence, but do not establish intrinsic gyro noise, drift or the
absence of onboard corrections. Published IMU8/LN200-family performance is not assigned
to these files.

The public [Applanix V6 interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
describes Group4 as time-tagged IMU data for POSPac and leaves its 24-byte sensor data
without engineering-unit definitions (printed page17). Its table of supported sensor
types/rates does not list the legacy type6. Header times identify validity in a selected
time base (printed pages7–8); that is not a definition of the underlying integration
period or latency. Group10002 describes a direct sensor stream with proprietary layouts
(printed pages64–65). None of the six files contains it. These structural descriptions
do not establish what corrections were applied to their Group4 channels.

| Required quantity | Evidence already preserved | Current support |
|---|---|---|
| Increment units | [Cross-date units checks](../ilvis0-imu6-cross-date-20261007/README.md) and [clock/installation checks](../ilvis0-installation-clock-20261007/README.md) | Empirical angle scale 0.4 arcsecond/count; candidate velocity scale 3.38e-5 m/s/count under nominal200Hz. Manufacturer scale table unavailable. |
| Axis mapping and mounting | Logged legacy settings reproduce the observed mapping changes. | Installation fields are inferred, not an authoritative legacy layout or surveyed mount. Initial orientation and mounting retain a gauge ambiguity. |
| Scale stability | Chronological checks against fused Group1. | Decoder evidence only. The October2010 gyro-scale holdout failure remains; fitted agreement is not independent sensor calibration. |
| Integration period | About200Hz cadence; alternating header jitter; fixed-period rate checks improve acceleration agreement. | Nominal-period and header-elapsed hypotheses remain distinct. The physical sensor clock has not been measured independently. |
| Physical IMU/GPS latency | Actual packet and receiver epochs are preserved. | Packet serialization offsets do not establish sensor latency. No supported numerical bound. |
| Gyro/accelerometer bias, gain and intrinsic noise | Raw increments and engineering-unit decoder comparisons. | No independently supported hardware-specific bounds. Software-control bounds and aircraft-motion variability are not specifications. |
| Earth-rate/transport-rate retention | Group4 exists, status fields are zero, Group10002 absent. | Correction status remains unknown; these facts do not prove retention or subtraction. |
| Coning, sculling, filtering, autozero and lever arms | Complete legacy messages/settings and earlier lever-arm diagnostics are preserved. | Processing conventions and precise lever-arm effects remain unsupported. A failed simple correction does not prove absence of processing. |
| GPS accuracy and temporal covariance | [GPS-only reconstruction](../ilvis0-position-20261007/README.md) and [error sensitivity](../ilvis0-gps-sensitivity-20261007/README.md). | Same-receiver consistency is established; independent coverage and systematic-error bounds are not. |

The archived raw integers, packet checksums, timing and setting epochs remain valuable.
At nominal200Hz, one angle count corresponds to a rate-equivalent 80 arcseconds/second;
that is quantization arithmetic, not a noise/drift specification or an averaging guarantee.
The velocity scale remains empirical. Neither a plausible gyro residual nor a successful
joint fit can certify corrections or calibration independently.

The next useful external evidence is a **legacy POS AV510/IMU6-specific** processing and
timing description, ideally tied to these firmware/installation epochs, or an independently
controlled calibration of the measurement chain. The needed answers are whether Group4
has Earth/transport rate removed; its integration and timestamp/latency conventions; its
bias/gain/filter/coning/sculling corrections; and hardware-specific calibration limits.
Modern type tables, an unrelated manufacturer's type6, and the IMU8 datasheet cannot supply
those answers. No manufacturer inquiry has been sent and none is authorized by this review.

Software work can continue with stated hypotheses, using longer and rotational controls
and preserving failures. Those controls cannot turn an assumption into independently
supported instrument evidence. The empirical fit gate and its unused allowance remain
unchanged; no fused navigation observable has been substituted for the raw IMU stream.

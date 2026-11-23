# The ESA score is most sensitive to north–south motion error

A constructed north–south position error alone can span the entire saved
two-minute score gap. It peaks at **17.6 cm** and requires **1.894 mm/s² RMS**
of acceleration in the saved position coordinates. Its position error is
zero at the four permanent Nuuk comparison times, and it ends at zero
position and velocity error. The construction measures the score’s
sensitivity. Actual aircraft motion and receiver error remain open.

| Allowed position-error directions | Acceleration that spans the saved gap, RMS |
| --- | ---: |
| North, east and up | 1.876 mm/s² |
| North and east | 1.892 mm/s² |
| North only | 1.894 mm/s² |
| East only | 37.678 mm/s² |
| Up only | 14.656 mm/s² |

North–south motion accounts for 98.1% of the acceleration energy and the
same share of the score change in the unrestricted construction. Even an
ideal vertical position measurement would leave the north-only case open.
This is a statement about position coordinates. A measured vertical force
can still depend on rotation, gravity and sensor tilt. [Original anchored path](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)

The separate GIRAFE file contains **1,200 consecutive 10 Hz samples** on
this exact comparison interval. Its atom half-interrogation time is 20 ms
throughout. The atom channel measures near-vertical specific force, and
the file also has two horizontal quartz accelerometer channels. Evaluating
the north–south direction with those channels requires their orientation,
alignment in time and in-flight error scale. As an indication of scale, a
tilt error of about 0.011° can put 1.9 mm/s² of gravity into a horizontal
accelerometer channel. The check used the force file only for time and
operating metadata. [GIRAFE data guide](../external-imu-data/ESA_GIRAFE_187.md) · [Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/#section2)

The outcome remains abstain. Thirteen tests passed. Both charged operations
completed with zero fits and zero reserved-flight reads. [Frozen plan](ESA_MOTION_AXIS_SUPPORT_PLAN.md) · [Sealed receipt](esa-motion-axis-support-result.json)

The [horizontal force follow-up](ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md)
found that measured disagreement and clock sensitivity exceed the expected
signal from the constructed error.

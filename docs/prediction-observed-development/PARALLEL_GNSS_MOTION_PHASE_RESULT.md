# When the late receiver difference grows

The [fixed receiver-speed split](PARALLEL_GNSS_MOTION_PHASE_PLAN.md)
reexamined all exact-time matches in the eighth window of the
[full comparison](FULL_PARALLEL_GNSS_V2_RESULT.md). Categories came only
from the `air1` receiver's measured speed. Fast means at least 50 m/s;
low speed means at most 0.5 m/s horizontally and 0.2 m/s vertically;
all other points are transition. Counts add exactly to the full-window
matches. No point was removed because of its receiver difference.

| Reference speed phase | `mosaic03` matches | `mosaic03` adjusted RMS N/E/U | `pwrpak7` matches | `pwrpak7` adjusted RMS N/E/U |
|---|---:|---:|---:|---:|
| Fast | 2,428 | **0.104 / 0.064 / 0.089 m** | 2,428 | 0.009 / 0.042 / 0.017 m |
| Transition | 370 | **0.248 / 0.240 / 0.240 m** | 370 | 0.016 / 0.032 / 0.017 m |
| Low speed | 1,207 | **0.468 / 0.388 / 0.589 m** | 915 | 0.014 / 0.046 / 0.041 m |

The `mosaic03` mean difference also grows in the same direction from fast
flight through transition to low speed. The final fixed window therefore
cannot be described as purely airborne: its largest discrepancy is at low
speed, although a smaller difference is already present during fast flight.
The other receiver stays closer to `air1` through all three phases.

This localizes a relative GNSS solution difference. It does not identify
which receiver is correct, the true aircraft position or the cause of the
drift. The receivers share an antenna and may share processing errors.
The [machine result](parallel-gnss-motion-phase-result.json) includes each
phase's matched time span, mean, centered RMS, 95th absolute percentile and
source hashes. Three focused software checks passed. No IMU, Earth-model fit
or reserved ESA group was used.

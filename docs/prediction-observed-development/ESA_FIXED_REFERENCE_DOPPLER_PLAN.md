# Direct GPS motion check at the Reykjavík stop

The [carrier and clock replay](ESA_FIXED_REFERENCE_CLOCK_RESULT.md)
leaves a vertical difference between two GPS reconstructions of the same
ground stop. Check whether the aircraft receiver’s direct Doppler measurements
show the same motion over the same period.

Use the sealed AIR1 and REYK00ISL excerpts, broadcast navigation and the
unchanged 61 comparison times from the [relative-phase
study](ESA_FIXED_REFERENCE_PHASE_RESULT.md). Keep its original ten GPS
satellites. Use L1 code to determine signal transmission time and L1 Doppler
to estimate motion. For every half-second AIR1 epoch, estimate the three
velocity components and a receiver clock drift. Use the original starting
GPS position to evaluate geometry throughout the ground stop, and integrate
the velocities with trapezoidal weights from zero displacement. Apply no
position updates, fitted trends or shifts. At the 61 comparison times,
compare signed positions and 30-second displacements with both the relative
carrier phase and the aircraft GPS solution.

Apply the same velocity solver to the fixed receiver using its published
position at its 61 observations. Report how much apparent velocity appears
on the fixed receiver. Its 30-second sampling only supports a sparse control
and cannot determine a common correction throughout the aircraft timeline.
The receivers share some satellite and atmospheric errors. Agreement here
can show whether Doppler corroborates either path on this stop. It cannot
calibrate the airborne error model.

Use one task on one numerical thread. Allow at most 3,601 aircraft solves
and 61 station solves, each with ten original satellite inputs. A complete
result requires the uninterrupted half-second aircraft grid, matching
station epochs and a full-rank velocity estimate at every epoch. Preserve
failures and report satellite counts and receiver clock drift. Technical
recovery only repeats an interrupted task under a separately charged
allowance. No additional downloads, aircraft IMU fits or reserved-flight
reads are authorized.

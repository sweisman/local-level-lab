# White gyro error versus changing gyro bias

The [channel control](ORACLE_CHANNEL_REPORT.md) finds that gyro errors drive
most horizontal forecast drift on two fixed generated IMU draws. The seeded
white-error and changing-bias arrays have since been reconstructed and shown
to reproduce both archived measured streams exactly.

Freeze four matched tasks: `increment-white`, `increment-bias`, `point-white`
and `point-bias`. In each task, add only that task's original gyro component
to the clean gyro increments, keep accelerometer increments clean, and use the
same 900-second physical trajectory and 900 receiver query times. Propagate
from the known starting state and calibration without fitting or future
receiver positions. Score reports 600–899 against independent analytic truth.

Stage one hash-bound clean stream and the four regenerated component arrays
before launch. Verify that each pair of components sums to its archived full
gyro stream. Each task permits one native forecast and 243 million
packet-query visits; use two single-thread workers, one-hour cooperative wall
limit, source/environment freeze and task-level reboot recovery. Preserve
completed results and charged failures. No ESA observed or protected group is
opened. The two draws are diagnostic, not a population noise estimate.

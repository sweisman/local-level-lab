# Which injected IMU channel drives the generated forecast drift?

The 900-second clean known-calibration forecast remains close to analytic
truth, while two saved noisy generated streams drift. This matched software
control keeps each archived noise draw and changes only which IMU channel
receives that draw:

| Task | Gyro increments | Accelerometer increments |
| --- | --- | --- |
| `increment-gyro` | Saved increment-noise stream | Clean stream |
| `increment-accel` | Clean stream | Saved increment-noise stream |
| `point-gyro` | Saved point-noise stream | Clean stream |
| `point-accel` | Clean stream | Saved point-noise stream |

Every task uses the same 900-second trajectory, 300 Hz packet times, known
initial state and sensor corrections, and 900 receiver query times. Score
reports 600–899 against analytic truth, without fitting or using later
receiver positions in propagation. Compare each result with the sealed clean
and full-noise forecasts. The split does not separate white noise from changing
bias, and nonlinear interactions mean the two channel errors need not add.

Freeze four task IDs, exact parent/input hashes, source/environment versions,
one native call and 243 million packet-query visits per task, two single-thread
workers, a one-hour wall limit, and task-level reboot recovery. Reconstruct the
clean increments once during preparation with a finite generation allowance;
bind that shared staged input to the completed clean-control array hashes.
Preserve
all charged failures and completed tasks. Do not read observed or reserved ESA
recordings. This is a software diagnostic, not a new Earth-model campaign.

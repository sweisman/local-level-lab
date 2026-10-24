# One ESA interval ready for the prediction pilot

**The first twenty-minute development interval is prepared and verified.**
It contains 360,029 original IMU samples and
360,028 constructed intervals, using actual timestamps.
The IMU is an inertial measurement unit containing gyroscopes and accelerometers.

The interval is the earliest eligible window in recording 187. It was chosen
before any ESA model fit. At the fixed query epochs, mean speed is
292.2 km/h, mean latitude is
64.19° N and height spans
1483–3526 m.
Turns and climbs remain in the data for explicit motion reconstruction.

The earlier **800 receiver positions** are stored for training. The later
**400 positions** are kept separately for scoring only after a continuous forecast
has been saved. Both working receiver-error cases use earlier observations only.
They are sensitivity assumptions, not calibrated receiver accuracy.

Preparation verified all 9,168,819 IMU rows and 64,080 receiver rows in one complete
pass through each source. The retained samples preserve original rate, acceleration,
temperature, timestamps and line numbers. Constructed angle and velocity increments
use the linear-point sampling hypothesis; they are not logged instrument increments.
Actual sampling, filtering and compensation remain distinct processing assumptions.

The saved-data audit checks every artifact hash, rate-to-increment conversion,
timing support, exact query indices, training/scoring separation, working weights
and charge journal. It does not reopen original sources or fit a model.

**No ESA globe/disc or background-field result exists yet.** The next gate is a
matched software check and a separately frozen 24-fit development comparison.
Seven confirmation groups remain protected. The original NASA findings are unchanged.

[Frozen preparation plan](PLAN.md) · [Pilot plan](../esa-development-pilot/PLAN.md) ·
[Source interval inventory](../esa-development-selection-v2/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

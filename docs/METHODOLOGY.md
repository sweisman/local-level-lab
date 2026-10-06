# How the experiment works

An **IMU (inertial measurement unit)** measures turning and acceleration. Its gyroscope measures
turning, while its accelerometer helps determine orientation.

The question is whether a separate IMU records the slow turning predicted by three
specific Earth models along a flight path: a rotating globe, a stationary globe, and a stationary
flat disc. The position record describes where the aircraft went. The gyroscope measures turning.
Each model is compared with the same recording.

The difficult part is separating the small signal from the instrument and aircraft. An IMU
can drift, its mount can move, and wind can make the aircraft point away from its direction of
travel. Allowing for these effects is essential, but a correction flexible enough to explain
anything can also explain away the signal. The experiment needs a route and procedure that
leave the models distinguishable after these uncertainties are included.

## Why carry a separate IMU?

The project uses a specified external IMU so that its settings and behavior can be examined
and compared between physical units. The phone records its Bluetooth messages and supplies
positions and times. A live display is useful for checking recording, but the scientific
analysis starts from the saved messages so others can inspect the decoding.

The hardware must first prove that it can preserve slow rotation. Some devices automatically
zero a steady gyro reading, which would erase the measurement of interest. A slow turntable
with a separately known rotation rate can test this without assuming any Earth model is correct.
See [Testing the instrument](BENCH.md).

## Why calibrate and turn the IMU?

A gyroscope can report a small nonzero rate even when there is no relevant turning. That error
can change over time and with temperature. Calibration before and after the flight helps
measure it and reveals changes during the recording.

The calibration uses repeated positions in reverse order. Facing the IMU the opposite way
changes the sign of some external turning signals while leaving some internal errors unchanged.
Keeping the same side up also keeps gravity acting in the same IMU direction. Repeating the
positions helps separate orientation effects from gradual drift.

Similar same-side-up turns during cruise can make useful differences in the flight measurements.
They must be slow, recorded and followed by secure mounting. Turning during an aircraft maneuver
can corrupt the reconstructed orientation; a timetable alone does not make a turn useful.
The analysis checks GPS for aircraft motion during each movement. If that check fails or
the position coverage is too sparse to verify it, the later orientation is treated as uncertain.

## Why do the route and wind matter?

On a globe, flying changes the direction of local down. On the particular flat disc being tested,
it does not produce that tilt, but travel around the disc still changes direction. Each model
must include its own motion prediction rather than treating the flat model as zero everywhere.

Wind adds another distinction: the aircraft can point sideways relative to the path it follows
over the ground. The IMU follows the aircraft, while GPS describes the ground path.
The analysis allows for that difference and tests more than one way it might vary.

A long straight flight can leave IMU drift and the model predictions too similar to separate.
Several headings can help, but only if the recording contains enough steady cruise on them.
Recent tests found that scheduling a leg at exactly the minimum permitted length can leave
almost nothing useful after the aircraft turn is excluded. Longer legs can also let changing
IMU error imitate slow signals. More flying is not automatically more information.

## How does the analysis decide whether there is enough evidence?

First it checks the recording and determines which parts are usable. Missing samples, uncertain
orientation and possible mount movement can exclude portions or the whole flight. Magnetic
measurements help check apparent mount movement, but changing wind can resemble it; the analysis
reports that ambiguity and retains its protective checks.

Next it asks whether differences between the Earth models survive the allowed IMU and wind
effects. The development method checks this at each model prediction rather than relying only
on whichever model the noisy recording happens to favor. Retained data and reconstructed IMU
orientation still affect that check, so it is not a guarantee based on the route alone.

An experimental extension repeats the calculation with different wind-related pointing errors,
uncertain forward direction and small changes in mounting direction. It keeps the weakest
model separation found. A schedule-search tool can compare when to turn the IMU on a fixed
route while avoiding aircraft maneuvers. These checks cover specified examples of uncertainty;
they do not guarantee success under every possible condition.

Only an informative recording can support a comparison. The method can report that one pair of
models is distinguishable while another pair is not. That partial evidence does not establish
a winner among all three. Its statistical decision rules still require independent validation.

## Why use simulations, and why are they not enough?

Simulated recordings let the software be tested when the generating model is known. Their motion
is calculated from a separate geometric construction, reducing the chance that the same mistake
appears in both the simulator and analyzer. Tests add wind, drift, temperature changes and losses.

Simulations are limited by what they assume. Real instrument measurements are still needed.
Development runs are used to find defects and choose a procedure. After those choices are fixed,
new runs will set decision thresholds, and a separate set will test the resulting error rate.
The same recordings cannot honestly serve all three purposes.

Public airline tracks can now supply the route for a simulated recording. One replay keeps
the original sparse position fixes and their missing accuracy information. Another assumes
a smooth path between nearby observations and generates simulated frequent GPS measurements
along it. Neither fills long gaps or treats provider estimates as observations. Wind changes
the simulated aircraft's pointing direction while the observed ground route stays fixed.
The generated IMU readings and frequent GPS remain assumptions, not measurements from that flight.

## Combining flights

Repeated recordings from one instrument share its errors. Combining them must preserve that
relationship rather than treating each recording as a new independent IMU. Different
instruments provide a stronger check, particularly if their results agree under different routes
and conditions. Experimental code also retains comparisons that a flight can support while
abstaining on comparisons it cannot; that pooling needs its own validated decision rules.

See [Evidence so far](EVIDENCE.md) for completed work and [Validation](VALIDATION.md) for what
remains. Equations are in [MATH.md](MATH.md). The detailed decisions, historical figures and
software checks are preserved in the [technical methodology record](METHODOLOGY_TECHNICAL.md).

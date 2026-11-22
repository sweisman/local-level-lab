# Five-hertz receiver motion context

## Question

On the already opened ESA recording 187, how much of the *changing* logged
body-down gyro rate tracks the course change reported by the GNSS-only PPP
receiver? This is a training-only motion diagnostic. GNSS course is not aircraft
heading; crab, bank, mount alignment, time tags and sensor error remain mixed
in any difference. No Earth-model fit, sensor-noise estimate or prediction
interval will be made from this comparison.

## Frozen inputs and selection

- The saved earlier-only 400 receiver rows from
  `data/esa-rolling-origin-400-development-v1-20261115` have input SHA-256
  `07bf133c016e9f4429827a3a1803487e2bed3df6a7728af2c5ec641deedee6c9`.
  Their GPS times run from 388214.9996717 through 388613.99964356 seconds.
- The saved six-channel rate input from
  `data/esa-training-rate-variation-20261024` has input SHA-256
  `41c03b1756e243b42abd04d081995244670c28dfad2aad0b225e7e96e1788a94`.
  Only its 119,865 IMU rows at or before the earlier-only cutoff are eligible.
- The separate `187_mosaic03_ppp_5Hz_final.txt` source has SHA-256
  `e6706cbe2971c25dc07d03446d8a77b9a48f673be0d967d1a8a11de59578555d`.
  Stream only through the earlier-only cutoff. Keep the 2,021 decoded rows
  starting five seconds before the first training report. Later receiver rows
  and all seven reserved ESA flight groups remain closed.

## Fixed calculation and limits

Use every saved training report time as a possible center. Compare fixed
two-second and ten-second spans separately. Find each GNSS endpoint from the
nearest 5 Hz observation within 0.11 second. Require no GNSS gap above 0.30
second. Average logged body-down gyro rates over IMU samples inside the same
span, with no IMU gap above 0.02 second and both edges supported within that
limit. Do not interpolate a missing sample or optimize a time shift. Unwrap
course circularly, calculate its endpoint change per actual elapsed time, then
report both rates in degrees per hour. Report the mean difference, the RMS of
the demeaned difference, correlation and every matched center. Overlapping
spans are descriptive, not independent replicates.

The known-motion software checks must pass before the recorded comparison.
For the recorded run, the technical support rule requires at least 350
matched centers at each span. A lower count is a retained technical failure;
the numerical values do not have a pass threshold. Freeze the staged arrays,
source and environment hashes, and this policy before execution. Use the
shared `lll.studies` lifecycle with two prepaid tasks, **zero native calls and
zero model fits**, one worker and one numerical thread, no retries and a
finite 10-minute wall allowance. The task result must say `abstain` for any
scientific decision. Preserve every rejected center and its reason.

This study may reveal low-frequency motion shared by the two data streams. It
cannot distinguish physical vibration above the receiver bandwidth from a
correlated sensor error, calibrate the forecast-error law, or release the ESA
confirmation groups. Those questions remain under the
[observed error plan](OBSERVED_ERROR_PLAN.md).

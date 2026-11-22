# The force-only result depends on how accelerometer gain is chosen

On both added NASA recordings, the earlier measurements allow gains that
clear every later one-sided force check for all four candidates. The earlier
[minimum-gain calculation](MATCHED_EXTENSION_FORCE_RESULT.md) reported misses
for three IMU8 candidates. In each case, an extra 0.11–0.12 percentage points
of gain clears those misses under the same receiver tracks and clocks.
This uses the later measurements to check compatibility across the allowed
range. It does not select a gain for prediction or alter any previous forecast.

| Recording | Candidate | Smallest gain allowed by earlier data | Smallest gain clearing both periods |
|---|---|---:|---:|
| IMU8 | Specified-field globe | 0.288% | 0.399% |
| IMU8 | Zero-field globe | 0.353% | 0.465% |
| IMU8 | Specified-field disc | 0% | 0% |
| IMU8 | Zero-field disc | 0.236% | 0.350% |
| IMU21 | All four candidates | 0.267–0.362% | Same as earlier |

The candidate force histories still differ after adjusting each candidate
by one allowed constant gain. The table shows the smallest achievable maximum
separation between the candidates' force intervals, in millimetres per second
squared. Each interval includes the original timing allowance. Each row requires
the same relative gain across all later windows, clocks and receiver tracks.

| Recording | Specified field | Zero field |
|---|---:|---:|
| IMU8 | 5.893 mm/s² | 5.116 mm/s² |
| IMU21 | 0.123 mm/s² | 0.245 mm/s² |

These values describe where the predicted force intervals stay apart under the
saved trajectory and gain assumptions. A shape test would also need a measured
error allowance at those times and a limit on how force changes within a packet.
The [paired-sensor study](PAIRED_ACCELEROMETER_RESULT.md) finds between-recorder
differences even after long averaging, on separate window boundaries. Their RMS
cannot serve as an error bound for these maximum gaps. The acceleration-only
shape decision remains open.

As a target for a uniform error bound, take the smallest gap across the six
individual clock and receiver choices. If one measured history can be within
an absolute error of each candidate at every window, the two force intervals
can be separated by at most twice that error. For this rule, errors below
2.89 and 2.51 mm/s² would prevent both shapes from fitting the IMU8 history
with the specified and zero fields, respectively. The corresponding targets
are 0.040 and 0.082 mm/s² on IMU21. A uniform bound at those levels would
still leave open whether either candidate fits the measurements.

Both tasks passed. All 36 operations used saved envelopes, with zero new fits,
propagations or reserved flights. [Frozen method](FORCE_GAIN_RANGE_PLAN.md) ·
[All gain and contrast results](force-gain-range-result.json) ·
[Verified evidence](force-gain-range-evidence/README.md)

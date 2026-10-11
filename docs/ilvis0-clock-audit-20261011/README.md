# Packet timing and independent calibration controls

**Both preselected recordings were reproduced from their original packet streams.**
This audit separates packet timestamp behavior from the unknown integration period of
the recorded increments. It identifies neither recording's physically correct clock.
Five small independently generated physical controls passed. There were **zero observed
fit starts and zero native navigation predictions**.

An **IMU (inertial measurement unit)** measures turning and acceleration. These two
recordings use IMU type 21 at declared rate code 2 (200 Hz), with the same previously
selected intervals. Their source hashes, native packet counts and first/last offsets
match the original fit provenance. Every source frame was checked for framing, declared
length and checksum. No timestamps or measurements were repaired or interpolated.
Group1 fused navigation was not used in this audit.

## Observed timing

The duration column is the public receiver-selected stretch. Native counts include
its frozen support guard. Mean period error compares header elapsed time with the
nominal period, not with an independently measured sensor integration period.

| Date | Selected minutes | Native increments | Interval scatter (µs) | Mean period error (ppm) | Total header − nominal (ms) | Adjacent interval correlation |
|---|---:|---:|---:|---:|---:|---:|
| 2015-10-05 | 7.30 | 87677 | 2.72 | 21.623 | 9.479 | -0.480 |
| 2015-10-25 | 7.22 | 86677 | 0.30 | 22.265 | 9.649 | -0.021 |

Both streams carry time-types code 2. The public [Applanix V6 ICD, Table 3 and
section 3.2.3](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
defines the primary tag as UTC and secondary type zero as POS time, elapsed since
power-on. Both tags describe validity time. Their differences provide a useful clock
comparison, although independent clock generation or the increment period is not established.

The roughly 22 ppm difference is about 0.0022%, around 900 times smaller than the
2% Z gyro-gain limit. It can matter greatly for accumulated height without directly
explaining the repeated large Z gain correction. Clock and calibration must be studied
together rather than treating the timestamp difference as the whole explanation.

| Date | POS-tag mean period error (ppm) | UTC elapsed − POS elapsed (ms) |
|---|---:|---:|
| 2015-10-05 | 17.896 | 1.634 |
| 2015-10-25 | 18.981 | 1.423 |

The report also retains interval extrema, cumulative drift extrema and effective rate. Compatibility
with a rounded time lattice is a diagnostic; it does not determine hardware resolution.

[Clock bins](clock-bins.csv) preserve every consecutive 200-packet block, including
partial final blocks, packet offsets, time span and sums of the original six signed
integers. These are compact timing checks, not new scientific fit intervals. Original
individual measurements remain in the retained source files. Detailed numerical values
and input/source/artifact hashes are retained beside this report.

## What the independent controls establish

Each timing control generates its increments from a known physical period, independently
of its packet tags. Stationary specific force cancels known gravity under the correct
integration convention. A known constant-rate angular prediction is checked against
the generated angle increments; raw angle increments are not multiplied by dt again.
All correct-clock maximum velocity and angular errors are below 10⁻¹⁰ in their units.

| Known construction | Wrong-clock maximum velocity error (m/s) | Wrong-clock maximum height error (m) |
|---|---:|---:|
| fixed_period_jitter | 0.001962 | 9.81e-06 |
| variable_period | 0.001962 | 9.81e-06 |
| clock_scale | 0.05886 | 3.53178 |

The controls show that fixed-period measurements with packet jitter need nominal timing,
whereas measurements genuinely accumulated over variable periods need elapsed timing.
A timestamp scale error can also create accumulated velocity and height error. These
are 120-second one-dimensional physical controls; their errors are not estimates of
NASA instrument error.

A further stationary control uses the actual selected UTC timestamp series, but
**synthetic force increments** accumulated over exactly 5 ms. With header timing it
produces the height changes below. A single analytically calculated gravity adjustment
matches mean duration; it is not a fitted NASA calibration.

| Date | Synthetic header-clock final height (m) | Mean-duration gravity adjustment (m/s²) | Maximum height after adjustment (m) |
|---|---:|---:|---:|
| 2015-10-05 | 20.363 | -0.00021212 | 0.0204 |
| 2015-10-25 | 20.505 | -0.00021842 | 0.0081 |

This demonstrates a timing/gravity trade-off on the observed time grid. It does not
establish that NASA increments span exactly 5 ms, or explain the actual nine-metre
vertical discrepancy in full. No observed accelerometer values enter this control.

The actual reoptimized control's gravity correction moved by about **+0.040 to
+0.042 m/s²**, while Z accelerometer offset and gain also changed. That is much larger
and opposite in sign to the simple stationary mean-duration adjustment above. The
[saved calibration audit](../ilvis0-clock-calibration-audit-20261011/README.md)
and hashed parameter-change input preserve those values. The single-channel illustration
therefore cannot identify the actual compensation path. A coupled three-dimensional
control and the matched profile study remain necessary.

For the independent scalar gyro equation, constant rotation leaves gain and offset
with rank one. Varying the known rotation raises their rank to two when the clock is
known: direct least squares and QR both recover the known predictions and parameters.
When clock scale is also free, three parameters still have only rank two. A second
gain/offset/clock tuple reproduces the same measured rate exactly to numerical precision.
Heading variation can improve gain–offset separation without independently resolving
clock scale. This scalar result does not establish the rank of the full GPS/IMU fit;
receiver timing and other measured channels may supply additional constraints.

## Next test

The [reoptimized clock comparison](../ilvis0-clock-trial-20261010/README.md) already
shows that recalibration repairs most of the fixed-parameter vertical error on the
control. The present timing audit and controls do not choose a clock from that better
fit. Next inspect accumulated-force and gyro sensitivities under the same calibration,
and qualify numerical methods on coupled physical controls before budgeting matched
joint Z gain–offset profiles. Use the [focused plan](../ILVIS0_DIAGNOSTIC_PLAN.md).
Neither the failed stopping trial nor the original corpus is resumed.

Reproduce this bounded audit:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-clock-audit-20261011/build_report.py
```

# How assumed GPS errors affect the airborne trajectories

The GPS sensitivity analysis is complete for the six prepared recordings and all 2,968
previously selected receiver epochs. It shows why more GPS positions do not automatically
give arbitrarily precise motion or position: persistent errors survive averaging, and
long windows can conceal the small, brief aircraft corrections the IMU must follow.
No Earth-model fit or new GPS position solve ran. All 232 stored originals remain.

This follows the [GPS-only reconstruction](../ilvis0-position-20261007/README.md).
That work produced positions from satellite code ranges and broadcast orbits. The new
analysis uses its frozen outputs, retaining every epoch and both methods. No fused
navigation, gyro values or Earth-model residuals enter the calculations or selection.

## Assumptions, not accuracy claims

Thirteen fixed cases are evaluated. One uses only the formal per-epoch covariance and
assumes independence across epochs. The other twelve add errors at three assumed sizes:
1/3, 3/10 and 10/30 metres, respectively for each horizontal axis and the vertical axis.
Each size is evaluated with independent errors or correlation times of 10, 60 and
300 seconds. Correlated errors use an exponential covariance in actual elapsed time.
Each case also has an independent constant offset and a linear drift whose endpoint
standard deviation equals the stated size. Those components and their axes are assumed
independent; the original formal covariance retains its cross-axis terms.

These sizes are an explicit sensitivity grid. They are **not independently established
error bounds, calibrated standard deviations or guaranteed coverage**. The analysis does
not select an assumption because it produces a favorable result. Same-receiver agreement
between positioning methods cannot constrain errors common to both methods.

For the mean position over each recording, the formal independent case gives horizontal
standard deviations of roughly 0.018–0.052 metres and vertical values of 0.046–0.086 metres
for L1. Adding the smallest 60-second correlated-error case with its offset and drift
raises these to about 1.20–1.22 metres horizontally and 3.60–3.65 metres vertically.
The increase is 23–79 times, depending on file and axis. This is the consequence of
the assumptions, not a measurement of the true error. A constant position error does
not average away, although it cancels from ideal fixed-frame derivatives.

## Position, velocity and acceleration require different checks

Fixed quadratic regressions evaluate velocity and acceleration in windows spanning
2, 6, 12, 30 and 60 seconds. Every fully supported centered window is retained; windows
at recording edges or across unsupported gaps are explicitly unavailable. Actual receiver
timestamps supply the weights. There is no interpolation, replacement, shortened edge
window or error-dependent smoothing choice. Both GPS methods use the same windows and
weights. Every assumed covariance propagates through those weights exactly.

The following ranges span the six recordings and the relevant axes. Acceleration is
in a fixed local frame at the first L1 position; it includes aircraft motion and route
geometry and is not an independent physical Earth observable.

| L1 acceleration diagnostic | 2-second window | 60-second window |
|---|---:|---:|
| Median formal horizontal standard deviation | 1.00–2.71 m/s² | 0.00037–0.00106 m/s² |
| Median formal vertical standard deviation | 2.61–4.50 m/s² | 0.00098–0.00177 m/s² |
| Median vertical standard deviation with smallest 60-second correlated case | 2.72–4.56 m/s² | 0.00472–0.00495 m/s² |
| RMS vertical difference between the two GPS methods | 1.22–2.27 m/s² | 0.00099–0.00272 m/s² |

The large improvement with longer windows is not permission to smooth away motion.
A deterministic control puts a one-second lateral velocity excursion, approximately
0.1 degrees at 200 m/s, into a trajectory. The two-second window retains its acceleration
response; the 60-second window attenuates it by more than a factor of 100. Long-window
uncertainties therefore describe the smoothed quantity, not sensitivity to brief motion.
No motion-screening rule or scientific eligibility gate was changed.

The practical conclusion is to preserve the native IMU increments and combine them with
GPS under explicit error assumptions. Differentiating these one-second code positions
alone does not establish reliable detection of tiny, brief attitude corrections. Conversely,
the IMU cannot automatically make GPS systematic errors or its own calibration disappear.

## Evidence and remaining work

[Mean-position sensitivity](mean-position-sensitivity.csv) contains 156 file/method/assumption
rows. [Kinematic sensitivity](kinematic-sensitivity.csv) contains 780 corresponding window
summaries. These are repeated views of six recordings, not independent trials. Full
per-window compressed exports stay in `data/ilvis0-gps-sensitivity-20261007/`.

Implementation: [sensitivity module](../../analysis/lll/ilvis0_gps_sensitivity.py) and
[worker](../../analysis/tests/ilvis0_gps_sensitivity_worker.py). Twenty-three focused tests
pass: ten new sensitivity tests and thirteen preceding positioning tests. They cover
dense covariance agreement, cross-axis terms, correlated means, coordinate conversion,
actual-time derivatives, constant-offset cancellation, gap/epoch/hash protection,
short-motion attenuation and corrupted resume receipts. The optional conventional-coordinate
covariance constructor is a conditional control tool; it does not satisfy an empirical
fit's independent receiver-covariance evidence prerequisite.

The run has its own source/input/environment manifest, source snapshots, atomic per-file
reports and hash-checked receipts. This evidence directory preserves the compact results
and snapshots. [export_inventory.py](export_inventory.py) verifies the completed evidence
and rebuilds the tables without rerunning the analysis. **Do not resume the completed
worker or revise its implementation under the same manifest.** Older studies remain frozen.

Next, establish support for the IMU6 integration clock, processing, calibration and mounting
assumptions, and carry correlated GPS errors into controlled joint IMU/GPS checks. Neither
this grid nor a promising fitted residual establishes that Earth rate remains in Group4.
The six-file empirical Earth-fit allowance is still unused; no scientific promotion,
downloads, original deletion or synthetic flight campaigns occurred.

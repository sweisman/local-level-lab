# Estimating motion from IMU readings and GPS

The bounded motion estimator is implemented. Five short, deterministic software controls
completed with no failures, and fifteen focused tests pass. The controls recover sensor
bias, effective orientation, gain and timing when the other relevant quantities are known.
They also expose an ambiguity when orientation and acceleration bias are both unknown.
No measured Earth-model fit ran, no scientific acceptance rule changed, and all 232
stored originals remain preserved.

## What the estimator does

An IMU measures rotation and specific force. Its acceleration channels include the effect
of gravity as well as aircraft motion. The estimator follows those readings through time
and predicts the position that the GPS antenna would occupy. It compares that prediction
with the actual receiver coordinates at their original timestamps.

Initial orientation and velocity, position offsets, gyro and accelerometer bias, gain,
gravity, antenna location and timing can be bounded nuisance parameters. Each bound must
be supplied explicitly. These controls do not establish appropriate bounds for any archival
instrument. An unknown constant mounting rotation and unknown initial orientation cannot
be separated from these observations alone; the estimator uses one effective orientation.

GPS uncertainty is supplied in the receiver's coordinate units, including correlations
between epochs when available. The same covariance applies to every candidate model;
changing the Earth-model distance metric must not change the observation weights. GPS
latitude, longitude and height retain their receiver conventions and are conditional inputs,
not independent raw satellite ranges or proof of a geometry.

The predictor can evaluate a position partway through a packet under its explicit
constant-rate/specific-force assumption. This does not interpolate or replace GPS/IMU
measurements. Receiver epochs must have IMU support throughout the entire allowed timing
offset. Unsupported gaps, duplicate epochs and invalid covariance are rejected.

## What the controls establish

These are two-second analytic translation controls at 100 Hz, with independently calculated
GPS positions. The assumed one-millimetre coordinate uncertainty is a software fixture,
not measured receiver performance. Other quantities are fixed when testing one parameter.
Varying acceleration tests gain and timing; it is not a flight campaign.

| Control | Known input | Recovered value |
| --- | ---: | ---: |
| Forward acceleration bias | 0.040 m/s² | 0.0400000001 m/s² |
| Effective initial tilt | 0.002 radians | 0.0019999991 radians |
| Accelerometer gain error | 0.003 | 0.00301347 |
| GPS/IMU timing offset | 0.035 seconds | 0.0349947 seconds |
| Tilt plus two acceleration-bias components | Three free quantities | Only two locally resolved directions |

The small gain/timing differences are within the declared control tolerances; midpoint
integration has finite-step error for changing acceleration. These tests establish software
recovery under stated assumptions, not archive-wide calibration accuracy. The ambiguity
control converges numerically but cannot identify all three parameters. Convergence alone
does not establish identifiability.

Numerical derivatives use steps scaled to the declared bounds. The diagnostic rank cutoff
also exceeds three times the discrepancy between two derivative step sizes. This prevents
roundoff in latitude/longitude from being treated as a newly identified parameter. It is a
local numerical diagnostic, not a calibrated statistical gate or formal error bound.

Every residual evaluation counts, including derivatives and the final rank diagnostic.
The five controls used 23, 21, 22, 18 and 64 evaluations respectively; each allowance was
160. The empirical entry point rejects missing independent evidence before charging a start.
Its append-only, locked and fsynced journal counts interrupted starts toward the separate
six-file, 24-start, 200-evaluation-per-start allowance. No empirical start was consumed here.

## Pairwise questions

The code supports a separate nuisance profile for each model pair, including globe versus
disc. Bounded calibration changes cannot automatically erase a contrast just because an
unbounded mathematical projection can. A test demonstrates the difference, and another
preserves one pair's information when a different pair has none.

A through-model calculation on the two-second software control evaluates all three
candidate anchors with common receiver weighting. This exercises the implementation; it
does not establish separation for an actual flight. The bounded tangent calculation is
local and varies one anchor at a time. It does not certify the separation of two independently
fitted nonlinear model families. Nonlinear pair profiles and numerical stability checks are
still needed before a scientific claim. Every present pairwise decision is abstention.

## These flights are not uniformly low and slow

NASA describes [LVIS](https://lvis.gsfc.nasa.gov/) as typically operating about ten kilometres
above the ground. Its [2010 Antarctic campaign](https://lvis.gsfc.nasa.gov/Data/Maps/AN2010Map.html)
used dedicated high-altitude DC-8 flights. Low-altitude survey flying is only part of this
archive's range.

The six prepared recordings have the following median values from embedded GPS. Heights
are above mean sea level, not terrain. Speeds are ground speeds from adjacent actual fixes,
using a conditional globe coordinate metric with altitude; they are not true airspeeds.

| Recording | Height | Ground speed |
| --- | ---: | ---: |
| 14 April 2009, LVIS | 6.88 km | 618 km/h |
| 16 September 2014, POS510 | 6.35 km | 586 km/h |
| 26 October 2010, LVIS | 10.40 km | 897 km/h |
| 20 November 2010, LVIS | 9.21 km | 937 km/h |
| 24 September 2015, LVISGH | 11.93 km | 793 km/h |
| 20 September 2017, B200T filename | 8.38 km | 482 km/h |

These summarize previously prepared stretches, not whole flights or confirmed lidar-on
intervals. The earlier 108 candidate windows span roughly 0.3–12.3 km altitude and
502–923 km/h. Their median window medians are 11.7 km and 806 km/h; this is not a
duration-weighted population median. Those broader summaries use fused navigation only
as labeled motion context. Simultaneous instrument recordings can overlap.

The predicted horizontal globe transport rate in those windows is 4.5–8.3 degrees/hour.
Slower travel reduces that curvature-related rate roughly in proportion to speed. Earth
rotation does not decrease with aircraft speed. Altitude affects the transport radius too,
but actual motion, sensor errors and processing still determine usable model separation.
The nominal scale failure in the 26 October 2010 recording remains explicitly recorded.

## What remains

The estimator now supplies the next tool, but its archive inputs still need independently
supported processing, clock, calibration and receiver-uncertainty evidence. Group-1 fused
navigation cannot supply the missing independent Earth observation. A plausible Earth-rate
residual would not itself establish which onboard corrections were applied. There is no
automatic transfer of passenger-protocol calibration to this permanently mounted IMU.

Work first on the six frozen representatives, then extend supported decoding and motion
checks by configuration to the other useful recordings. Empirical Earth fitting stays
limited to its separately authorized scope and requires the evidence gate before any start.
Once the archival analysis is ready, the intended project direction is to make it primary
and present the passenger IMU experiment as a secondary extension. Instrument-specific
quality and fast flight are promising inputs; neither substitutes for the remaining checks.

Implementation: `analysis/lll/ilvis0_estimator.py` and `ilvis0_estimator_controls.py`.
Launcher: `analysis/tests/ilvis0_estimator_worker.py`. Completed output:
`data/ilvis0-estimator-20261007/`. This evidence directory preserves the manifest, source
snapshots, complete compressed results, completion and the control-start journal. The
completed run must not be resumed or combined with a revised implementation.

# The math

All rates are angular velocities in rad/s, expressed in the local **NED** frame (north, east, down) unless noted. Reports convert them to °/h (1 rad/s = 206 264.8 °/h).

## What a gyro measures

A gyro measures the phone's angular velocity relative to **inertial space** (any non-rotating reference frame; the gyro senses this mechanically, it doesn't look at anything), in the phone's own axes:

```
ω_ib = C_bn · ω_in  +  ω_nb  +  bias  +  noise
```

- `ω_in` is the rotation of "local level" (the north-east-down frame at the aircraft's position) relative to inertial space. **This is what the four models predict.**
- `ω_nb` is the phone's rotation relative to local level, meaning the aircraft's own pitching, rolling and turning.
- `C_bn` rotates NED vectors into phone axes.

## The four models

`ω_in` is split into two physically separate terms, **Earth rotation** and **transport rate** (the rotation of local level caused by moving over a curved surface):

| | Earth-rotation term | Transport term |
|---|---|---|
| **Sphere, rotating** | `Ω (cos φ, 0, −sin φ)` | `ω_en` |
| **Sphere, still** | 0 | `ω_en` |
| **Flat, rotating** | `(0, 0, −Ω)` | 0 |
| **Flat, still** | 0 | 0 |

- `Ω = 7.2921150 × 10⁻⁵ rad/s` (one turn per sidereal day, 15.041 °/h). `φ` is the latitude.
- **Flat, rotating** is a disc spinning about its centre (the north pole) at the same sidereal rate. Its rotation axis is vertical everywhere, so a phone anywhere on it sees the full Ω about local vertical and nothing horizontal.
- **Transport rate** on the WGS-84 ellipsoid is

  ```
  ω_en = ( v_E / (R_N + h),  −v_N / (R_M + h),  −v_E tan φ / (R_N + h) )
  R_M = a(1−e²) / (1 − e² sin²φ)^{3/2}      R_N = a / (1 − e² sin²φ)^{1/2}
  ```

  On a plane, the radius is infinite and the term is zero.
- Examples: 224 m/s (500 mph) due north at the equator gives `|ω_en| = 3.54 × 10⁻⁵ rad/s = 7.29 °/h`. A typical airliner cruise of 900 km/h (250 m/s) gives `3.92 × 10⁻⁵ rad/s ≈ 8.1 °/h`.

### Sign conventions, checked

NED is right-handed (N × E = D), and a rotation vector ω turns any frame-fixed vector **r** at `dr/dt = ω × r`.

- **Earth rate.** The spin axis points to the north pole. At latitude φ that axis is `cos φ` north and `sin φ` *up*, so the down component is `−sin φ`. At the north pole, ω_ie = (0, 0, −Ω): the rotation is about "up", counter-clockwise seen from above. That's the true sense of Earth's rotation.
- **Transport, moving north.** ω_en = (0, −v/R, 0), a rotation about west. The local down vector then changes at `ω × D = (−v/R)(E × D) = −(v/R) N`. Down tilts south, so up tilts north. That's right: the radius vector swings towards the direction of travel.
- **Transport, moving east.** ω_en = (v/R, 0, −v tan φ / R). The north component tilts up towards the east. The down component is the meridian convergence: a constant-course (rhumb) track turns relative to inertial space.

The same formulas are implemented independently in Python (`analysis/lll/models.py`) and Kotlin (`model/Transport.kt`). Both are tested against `docs/test_vectors.json`, and Python is also tested against the hand-computed headline numbers above.

Altitude barely matters (11 km is 0.2 % of R). Speed and recording time are what count.

## Ground calibration (4 positions)

The phone lies still in four positions: face up, face up turned 180° about vertical, face down, face down turned 180°. Any rotation that's constant in the local frame projects onto the phone axes with signs that cancel across the four:

```
bias  = mean of the 4 position means
w_i   = g_i − bias                       (rotation seen in position i)
up_i  = accelerometer direction (the plumb line, model-independent)
rotation about up    = mean_i (w_i · up_i)
horizontal magnitude = mean_i |w_i − (w_i · up_i) up_i|
```

This needs no compass or heading. It's a ground-level test of its own. At latitude φ the predictions are:

| model | about up | horizontal |
|---|---|---|
| sphere, rotating | Ω sin φ | Ω \|cos φ\| |
| flat, rotating | Ω | 0 |
| still (either shape) | 0 | 0 |

Pooled across many contributors at many latitudes, the collation fits `up = A sin φ + B` and `horizontal = C |cos φ|`.

- A rotating globe gives A = C = 15.04 and B = 0.
- A rotating disc gives A = C = 0 and B = 15.04.
- A still Earth gives all zero.

The horizontal magnitude is a norm, so noise biases it upward. A phone with no horizontal rotation still shows a few °/h.

## In flight

The flight is cut into **stable cruise** segments: speed above 100 m/s, |vertical speed| under 1.5 m/s, |turn rate| under 0.05 °/s, low vibration, a good GNSS fix, and at least 10 minutes each. Each segment is averaged into 60-s bins.

For each bin:

1. **Up** in phone axes `u` comes from the mean accelerometer direction.
2. The **forward axis** comes from banked turns anywhere in the flight. In a coordinated turn, `bank = atan(v ψ̇ / g)`, and rolling happens about the aircraft's longitudinal axis. So the horizontal gyro component regressed on the GNSS-derived bank rate gives the forward axis in phone coordinates. Its azimuth is the GNSS course.
3. **Aircraft rotation relative to level** is `ω_nb = (du/dt) × u − ψ̇ u`. The first term is the tilt rate the accelerometer sees, such as pitch-trim drift as fuel burns. The second is the GNSS course rate about the vertical.
4. Calibrated bias `b_cal(t)` is interpolated linearly between the pre- and post-flight calibrations.
5. **Temperature.** The phone usually runs warmer in flight than during calibration, and MEMS gyro bias depends on temperature. If cruise battery temperature differs from the calibration mean by 2 °C or more, the fit adds a per-axis coefficient `c` (bias change per °C) with a Gaussian prior. Its width comes from the drift runs if they spanned a temperature range, otherwise 5 °/h/°C.

Then

```
y = m − b_cal(t) − ω_nb  =  b_res + C_bn (k_rot·E_sphere + k_rotflat·E_flat + k_curv·T) + noise
```

Each bin gives three rows in phone axes. There are six unknowns, or nine with the temperature term (`+ c·(T − T_cal)`): three residual-bias components `b_res`, three scale factors `k`, and optionally the three `c`. Weighted least squares fits them, with a Gaussian prior on `b_res` whose width comes from how far the bias moved between calibrations.

- **The k values** give each term's measured strength. Expected values are rotating sphere (1, 0, 1), still sphere (0, 0, 1), rotating flat (0, 1, 0), still flat (0, 0, 0). The confidence intervals are the larger of the analytic value and a moving-block bootstrap over bins, since bias wander correlates neighbouring bins.
- **Model comparison** fixes each model's k vector, refits only `b_res`, and reports χ² for each. Δχ² against the best model and the relative weights `exp(−Δχ²/2)` are reported too.
- **Accumulated rotation** integrates `C_nb y` over each segment, with no fitted terms, and sets it beside each model's integrated prediction.

### What feeds the prediction, and what feeds the measurement

The prediction of each model, `ω_in` in NED, is computed **only from GNSS**: latitude, altitude, north and east velocity. No gyro data goes into it.

To compare it with the gyro, the prediction has to be expressed in phone axes, so the analysis needs the phone's orientation relative to NED:

| quantity | source | uses the gyro? |
|---|---|---|
| model prediction `ω_in` (NED) | GNSS | no |
| up axis `u` | accelerometer | no |
| azimuth | GNSS course | no |
| forward axis in phone coordinates | gyro **roll rate during banked turns**, correlated with GNSS bank angle | yes, only the large roll transients (°/s), never the slow signal (°/h) |
| aircraft rotation `ω_nb` | accelerometer tilt rate + GNSS course rate | no |
| calibrated bias | stationary gyro on the ground | yes, ground data only |

The forward-axis step only fixes which phone direction points along the fuselage. It takes no magnitude from the gyro, and it is the same for all four models, so it can't favour one model over another.

### Why turns, calibration and drift runs matter

On one straight leg, the phone's orientation relative to NED barely changes. The predicted signal is then nearly constant in phone axes, which is exactly what a constant bias looks like. Three things separate them:

- the calibration prior, plus pre/post drift and the drift runs;
- heading changes, which rotate the predicted vector into different phone axes while the bias stays put;
- 180°-rotated control runs, and pooling many flights on different headings and latitudes.

The report shows the largest correlation between bias and k, so readers can see how well a given flight separated them.

### Fallback: vertical only

With no usable banked turns, the forward axis is unknown. The fit then uses only the component along the plumb line, which needs no heading. That still separates the rotating models on most routes, but it has blind spots. For example, eastbound at mid-latitudes the globe's `Ω sin φ + v_E tan φ / R` can come close to the disc's Ω.

### Known approximations (please review)

- The aircraft's heading is taken from its GNSS course, so crab angle (a few degrees) rotates the horizontal predictions slightly.
- The vertical-channel correction `ψ̇` uses the GNSS course rate in WGS-84 coordinates. For the flat models, "heading" over the ground is defined differently. That only affects the vertical rows, and only while the course is changing, and turning bins are already excluded.
- The accelerometer's plumb line includes the small Coriolis and centripetal terms (~0.2°). They are nearly constant through cruise, so they barely affect `du/dt`.
- Battery temperature stands in for sensor temperature. The sensor can lag or lead the battery, so the temperature term is only an approximation.
- **Slow yaw slip in the mount is the hardest error to catch.** If the phone creeps about the vertical, the accelerometer can't see it, and the creep rate goes straight into the vertical channel. In simulation:
  - slips up to 3 °/h still recovered all four truths;
  - at 8 °/h a flat-rotating truth was misread as flat-still.

  Tilt slips are caught by the accelerometer and don't matter. The uncalibrated magnetometer is recorded in every session and could detect yaw slip relative to the airframe. That's future work.

## Validation

`analysis/lll/synth.py` generates complete sessions in the app's exact file format, with any of the four models as ground truth. They include realistic gyro noise (BMI270-class, 0.007 °/s/√Hz), bias offset, drift and random walk, pitch-trim drift, coordinated banked turns, and GNSS noise. The test suite checks that the pipeline recovers each truth: the correct model wins and the k values match within their CIs. It also checks that calibration recovers the injected bias and ground Earth rate.

**Adversarial simulations** add the conditions a real flight brings: temperature-dependent bias with the phone warming 8 °C in flight, turbulence bursts (real attitude jitter and vertical bumps), slow tilt slip in the mount, climb and descent, and GNSS dropouts. Each was run on its own and all together, for all four truths (seed 7). Recovered = correct model wins and every k is within 3.5σ of its expected value.

| condition | recovered | note |
|---|---|---|
| temperature-dependent bias, with temperature term | 4/4 | k_curv 0.98 ± 0.19 for a curved truth |
| same, temperature term disabled | 4/4 | k_curv biased to 0.72 and −0.29, about 1.4σ off |
| turbulence bursts | 4/4 | turbulent minutes excluded automatically |
| tilt slip 2 °/h | 4/4 | |
| yaw slip 1 / 3 / 8 °/h | 4/4 / 4/4 / 3/4 | see Known approximations |
| climb and descent | 4/4 | |
| GNSS dropouts | 4/4 | segments split at gaps |
| all of the above at once (yaw slip excluded) | 4/4 | flat-rotating vs flat-still separate only weakly in flight (Δχ² 4–8); ground calibration separates them |
| no calibration at all | flagged | k intervals widen; not confidently wrong |

The combined case, the temperature-term comparison and the no-calibration case are part of the automated tests (`analysis/tests/test_analysis.py`).

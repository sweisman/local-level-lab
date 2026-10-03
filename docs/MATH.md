# The math

All rates are angular velocities in rad/s, expressed in the local **NED** frame (north, east, down) unless noted. Reports convert them to °/h (1 rad/s = 206 264.8 °/h). The reasons behind each choice, the alternatives rejected and the simulation evidence are in [METHODOLOGY.md](METHODOLOGY.md). The numbers come from [EVIDENCE.md](EVIDENCE.md).

## What a gyro measures

A gyro measures the IMU's angular velocity relative to **inertial space** (any non-rotating frame). It senses this mechanically and doesn't look at anything. In the IMU's own axes:

```
ω_ib = C_bn · ω_in  +  ω_nb  +  bias  +  g-sensitivity · f  +  noise
```

- `ω_in` is the rotation of local level (the NED frame at the aircraft's position) relative to inertial space. **This is what the models predict.**
- `ω_nb` is the IMU's rotation relative to local level: the aircraft's own pitching, rolling and turning.
- `C_bn` rotates NED vectors into IMU axes.
- `f` is the specific force the accelerometer measures, about 1 g along up. Real MEMS gyros have a small error proportional to it: g-sensitivity.

## The three models

| | Earth rotation | Transport (moving over the surface) |
|---|---|---|
| **Globe, rotating** | `Ω (cos φ, 0, −sin φ)` | `ω_en` (globe) |
| **Globe, still** | 0 | `ω_en` (globe) |
| **Flat disc, still** | 0 | `ω_disc` |

- `Ω = 7.2921150 × 10⁻⁵ rad/s`, one turn per sidereal day (15.041 °/h). `φ` is the latitude.
- **Globe transport**, on the WGS-84 ellipsoid:

  ```
  ω_en = ( v_E / (R_N + h),  −v_N / (R_M + h),  −v_E tan φ / (R_N + h) )
  R_M = a(1−e²) / (1 − e² sin²φ)^{3/2}      R_N = a / (1 − e² sin²φ)^{1/2}
  ```

  For example, 224 m/s due north at the equator gives 7.29 °/h. At 900 km/h (250 m/s) it is 8.1 °/h.
- **Disc transport.** The flat model is an azimuthal-equidistant disc centred on the north pole, with latitude as distance from the centre and north pointing to the centre. Moving east means circling the centre, so local level turns about the vertical once per 360° of longitude:

  ```
  ω_disc = ( 0,  0,  −dλ/dt ),      dλ/dt = v_E / ((R_N + h) cos φ)
  ```

  The second formula only undoes the receiver's conversion of the coordinate rate into metres per second. It uses no globe geometry and doesn't depend on the disc's scale. The disc never tilts local level, so there is no horizontal part.
- **No spinning disc.** The flat model assumes no rotation. A constant spin about the vertical couldn't be measured anyway (see "The vertical channel").

### Sign conventions, checked

NED is right-handed (N × E = D), and a rotation vector ω turns a frame-fixed vector at `dr/dt = ω × r`.

- **Earth rate:** the spin axis is `cos φ` north and `sin φ` up, so the down component is `−sin φ`.
- **Moving north on the globe:** `ω_en = (0, −v/R, 0)`. Down then changes at `−(v/R) N`, so up tilts north, towards the direction of travel.
- **Moving east:** on the globe, local level tilts (north component `v/R`) and turns at `−v tan φ / R` about the vertical (meridian convergence). On the disc it only turns, at `−dλ/dt`.

**Independent check.** `analysis/tests/truthgen.py` computes `ω_in` from frame geometry alone. It builds the NED axes at each position in an inertial frame and differentiates their orientation numerically, with no transport or Earth-rate formula. All three models agree with it to 9 × 10⁻¹² rad/s (EVIDENCE §1). Synthetic test data takes its gyro truth from this generator, never from `lll.models`. The same formulas are implemented in Kotlin for the live display and checked against `docs/test_vectors.json`.

### Which measurement separates which models

At 40°N, 230 m/s due east:

| | globe, rotating | globe, still | disc |
|---|---|---|---|
| horizontal | Ω cos φ + v/R tilt | 7.4 °/h tilt | 0 |
| vertical | −sin φ (Ω + dλ/dt) ≈ −16 °/h | −6.2 °/h | −9.7 °/h |

- **Earth rotation in globe form** has a horizontal part, and one flight with heading changes settles it to ±0.04.
- **Globe against disc transport** is decided by the horizontal tilt. The vertical rates are similar.

## The vertical channel

A rotation about the plumb line points along gravity. So does the gyro's g-sensitivity along that axis, and so does its bias along whichever IMU axis points up. In level flight, with the IMU's attitude fixed, all three are constants on the same IMU axis. Neither a stationary test nor level flight can separate them. Only changes in size, along the route or across latitudes, carry information. This is why a spinning disc can't be tested, and why the disc's own vertical term is identified only through how dλ/dt changes along the route.

## Ground calibration

The IMU lies still in four positions: label up, label up turned 180° about the vertical, label down, and label down turned 180°. The app records them as a palindrome, each position twice in mirror order: up0 up180 down0 down180 (one double-length stay) down0 up180 up0. For each visit k, per axis:

```
m_k = b + d (t_k − t̄) + w_{p_k},     Σ_p w_p = 0
```

- **`b`, the bias.** Earth rotation and gravity-dependent error both reverse between the up and down pairs or within the 180° pairs, so they cancel out of b.
- **`d`, a linear drift.** Every position's visits average to t̄, so d is orthogonal to the position effects.
- **Horizontal Earth rate:** `h = |(w_0 − w_180)/2|`, after removing the part along up, taken from each 180° pair. Within a pair gravity sits on the same IMU axis, so g-sensitivity is identical and cancels. The Earth's horizontal component reverses. The globe predicts Ω|cos φ|; a still globe or the disc predicts 0. Noise biases a norm upward, so the estimate subtracts the expected noise power.
- **Vertical:** `(w_0 + w_180)/2 · up`. This is the vertical Earth rate plus g-sensitivity along gravity, which can't be separated, and the result is marked as aliased.
- **IMU magnetic offset:** the mean magnetometer reading over the four positions is the field fixed in the IMU (hard iron), because the Earth's field cancels the same way.

## In flight

### Segments and bins

The flight is cut into stable cruise segments, each at least 10 minutes long:

- speed above 100 m/s;
- |vertical speed| under 1.5 m/s;
- |turn rate| under 0.05 °/s;
- low vibration;
- a good GNSS fix.

Segments also break at GNSS gaps, Bluetooth drops, bumps and deliberate IMU turns. Each segment is averaged into 60-s bins.

### The IMU's orientation

| quantity | source | uses the gyro? |
|---|---|---|
| model prediction `ω_in` (NED) | GNSS: latitude, height, north and east velocity | no |
| up axis | accelerometer | no |
| azimuth | GNSS course | no |
| forward axis | gyro roll rate during banked turns, correlated with the bank GNSS implies | only the large roll transients (°/s), never the slow signal (°/h) |
| aircraft rotation `ω_nb` | accelerometer tilt rate and GNSS course rate | no |
| turns of the IMU itself | gyro, integrated over the few seconds of the turn | only the turn itself (tens of °/s) |

Each deliberate turn of the IMU starts a new **mount epoch**. The gyro integrates the rotation during the turn to within about 0.1° (EVIDENCE §10). Later epochs are mapped back into the first epoch's frame, so banked turns anywhere in the flight give one forward axis.

### The fit

For each bin:

```
y = m − b_cal(t) − ω_nb  =  C_bn (k_rot·E_globe + k_curv·T_globe + k_disc·T_disc)  +  b_res[g]  +  noise
```

- **`b_cal(t)`** is interpolated linearly between the pre- and post-flight calibrations.
- **`b_res[g]`** is a residual bias for each gravity orientation g.
  - Bins whose up directions agree within about 25° share one.
  - A flip, or any turn that moves gravity to another IMU axis, starts a new one, because g-sensitivity changes with it.
  - Its Gaussian prior combines in quadrature: half the pre/post change, the calibration error, a 1 °/h floor, 5 °/h for vibration rectification and 5 °/h for g-sensitivity. The ground calibration sees neither of the last two.
- **Temperature:**
  - If cruise chip temperature differs from calibration by 2 °C or more, for most bins, a per-axis coefficient times (T − T_cal) is added.
  - When a drift run measured the coefficient, it is applied, and only the residual is fitted, with a prior of ±30 %.
  - Otherwise the coefficient is fitted freely. The analysis then also reports k without the term and flags `temperature_sensitive` if any k moves by more than 1σ.
- **Each bin gives three rows**, or one in vertical-only mode. Weighted least squares fits the three k values and the nuisance terms.

Expected k for each model, in the order (k_rot, k_curv, k_disc): rotating globe (1, 1, 0), still globe (0, 1, 0), disc (0, 0, 1).

### Uncertainty and model tests

- **k intervals** are the larger of the analytic value and a moving-block bootstrap over bins. Bias wander correlates neighbouring bins.
- **χ²** is scaled by `(1 − ρ)/(1 + ρ)`, the effective-sample factor from the lag-1 autocorrelation of bin residuals within segments.
- **Each model is tested against the free fit.** Fix its k values, refit the nuisance terms, and compare. `Δχ²` follows χ² with 3 degrees of freedom if that model is true. A model is **rejected at p < 0.0027 (3σ)**. Bootstrap ranges of Δχ² are reported. Relative likelihoods `exp(−Δχ²/2)` are shown, labelled as not probabilities.
- **Identifiability.** For each term: the fraction of its predicted signal that a constant residual bias per gravity orientation could mimic, `sqrt(1 − |r|²/|x|²)`, where r is the term's column after regressing out the bias columns. Near 1 means only the bias prior constrains it. Above 0.95 for k_curv flags `k_not_identified`.
- **Prior sensitivity.** Refit with the bias prior 3× wider. If any k moves by more than 1σ, the flag is `prior_dominated`.
- **Vertical-only fallback.** With no banked turn, the forward axis is unknown and only the vertical channel is used. On a straight leg that channel can't identify anything (see "The vertical channel"), and the analysis says so.

### Mount slip watchdog

A slow turn of the IMU in its mount about the vertical goes straight into the vertical gyro channel. The accelerometer can't see it, but the magnetometer can. The horizontal field, in a level frame fixed to the IMU, is modelled as complex numbers:

```
z(t) = e^{iδ(t)} ( s(t) e^{iθ(t)} H + c ),     θ = ψ − D
```

- `ψ` is the GNSS course and `D` the declination.
- `s(t)` is the change in horizontal field strength along the route.
- `H` and `c` are the Earth's and the airframe's fields. Both turn with the airframe.
- The IMU's own magnetic offset is removed first, using the ground calibration.
- Each bin is projected with its own measured up, so pitch changes can't leak the strong vertical field into the horizontal.
- `H` and `c` are fitted per mount epoch from the aircraft's heading changes. With less than 45° of heading change, `c = 0` is assumed and the result says so.

The slip rate `δ̇` is the slope of the leftover angle in each segment. A segment is excluded when the slip exceeds 2 °/h and 3σ.

The watchdog runs twice. One version uses `D` and `s` from the World Magnetic Model, which is built on a globe. The other uses none, with `D` constant and `s = 1`. A segment is left out of the gyro fit only when both detect slip, and both results are reported. The gyro fit itself never uses the magnetometer.

## Pooling many sessions

Sessions with the same IMU share its quirks, so pooling is hierarchical, with DerSimonian–Laird random effects at each level:

```
sessions → per IMU unit → population of units
```

Each level adds the scatter between its members (τ²) to their error bars. Each model's expected k is then tested against the pooled k: χ² with 3 degrees of freedom, rejected at p < 0.0027.

Only sessions that pass every gate enter the primary result:

- both calibrations;
- at least 60 minutes of cruise;
- curvature identified;
- not prior-dominated;
- an IMU unit rated qualified or usable;
- not synthetic.

Breakdowns by heading, mount, IMU variant and unit are consistency checks. Groups that disagree (heterogeneity p < 0.01) are flagged, never averaged away.

**Ground results across latitudes:**

- **Horizontal (primary):** `h = C |cos φ|`. A rotating globe gives C = 15.04, a still globe or the disc gives C = 0.
- **Vertical:** `up = A sin φ + B_unit`, with one intercept per IMU unit, because each unit's g-sensitivity along gravity is unknown. A is informed only by units calibrated at more than one latitude.

**Unit quality tiers** use instrument criteria only, never which model wins:

| tier | requirement |
|---|---|
| qualified | bias instability ≤ 5 °/h on the worst axis, from a still run of 25 minutes or more, and ground horizontal σ ≤ 2 °/h |
| usable | ≤ 10 °/h and ≤ 4 °/h, where measured |
| exploratory | anything else |

## Known approximations (please review)

- **Crab angle.** The aircraft's heading is taken from its GNSS course, so a crab angle of a few degrees rotates the horizontal predictions slightly.
- **Plumb line.** The accelerometer's plumb line includes small Coriolis and centripetal terms, about 0.2°. They are nearly constant in cruise.
- **Quantization.** At the default ±2000 °/s range, one 16-bit count is 220 °/h. Noise dithers it, but coarse counts still interact with constant offsets at the °/h level (EVIDENCE §4). A finer range should be used if the device allows one.
- **Temperature.** Chip temperature is reported by the IMU's firmware. A lag, or a nonlinear response, shows up as `temperature_sensitive`.
- **Device processing.** WitMotion firmware applies factory calibration and filtering before the data leaves the device (see FORMAT.md).
- **Vertical-channel limits.** See "The vertical channel" above.

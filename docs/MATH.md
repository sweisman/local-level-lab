# The math

This is the mathematical reference for readers checking the equations. Start with the
[plain-language methodology](METHODOLOGY.md) for the flight signal and measurement procedure.
An IMU (inertial measurement unit) combines instruments for measuring turning and acceleration.

All rates are angular velocities in rad/s, expressed in the local **NED** frame (north, east, down) unless noted. Reports convert them to °/h (1 rad/s = 206 264.8 °/h). The reasons behind each choice, the alternatives rejected and the simulation evidence are in [METHODOLOGY.md](METHODOLOGY.md). Historical numerical tables are in [the technical evidence record](EVIDENCE_TECHNICAL.md); [Evidence so far](EVIDENCE.md) explains their limits and the current results.

## What a gyro measures

A gyro measures the IMU's angular velocity relative to **inertial space** (any non-rotating frame). It senses this mechanically and doesn't look at anything. In the IMU's own axes:

```
ω_ib = C_bn · ω_in  +  ω_nb  +  bias  +  g-sensitivity · f  +  noise
```

- `ω_in` is the rotation of local level (the NED frame at the aircraft's position) relative to inertial space. **This is what the models predict.**
- `ω_nb` is the IMU's rotation relative to local level: the aircraft's own pitching, rolling and turning.
- `C_bn` rotates NED vectors into IMU axes.
- `f` is the specific force the accelerometer measures, about 1 g along up. Real MEMS gyros have a small error proportional to it: g-sensitivity.

## The models: four defined, three tested

Four kinematic models are defined. Three of them can be told apart by this protocol, and those three are the ones the analysis tests.

| | Earth rotation | Transport (moving over the surface) | tested? |
|---|---|---|---|
| **Globe, rotating** | `Ω (cos φ, 0, −sin φ)` | `ω_en` (globe) | yes |
| **Globe, still** | 0 | `ω_en` (globe) | yes |
| **Flat disc, still** | 0 | `ω_disc` | yes |
| **Flat disc, spinning** | `(0, 0, −Ω)`, about the vertical everywhere | `ω_disc` | no: indistinguishable from the still disc (see below) |

- `Ω = 7.2921150 × 10⁻⁵ rad/s`, one turn per sidereal day (15.041 °/h). `φ` is the latitude.
- **Globe transport**, on the WGS-84 ellipsoid:

  ```
  ω_en = ( v_E / (R_N + h),  −v_N / (R_M + h),  −v_E tan φ / (R_N + h) )
  R_M = a(1−e²) / (1 − e² sin²φ)^{3/2}      R_N = a / (1 − e² sin²φ)^{1/2}
  ```

  For example, 224 m/s due north at the equator gives 7.29 °/h. At 900 km/h (250 m/s) it is 8.1 °/h.
- **Disc transport.** The flat model is an azimuthal-equidistant disc centred on the north pole, with latitude as distance from the centre and north pointing to the centre. Moving east means circling the centre, so local level turns about the vertical once per 360° of longitude:

  ```
  ω_disc = ( 0,  0,  −dλ/dt )
  ```

  The analysis takes dλ/dt straight from the logged GNSS longitudes, differentiated with 30-s smoothing, so the disc's prediction uses no velocity, no Earth radius and no disc scale. Westbound, dλ/dt is negative and local level turns the other way. The disc never tilts local level, so there is no horizontal part. The app's live display, which has only the current fix, uses the equivalent v_E / ((R_N + h) cos φ).
- **Why the spinning disc isn't tested.** It differs from the still disc only by a constant rotation about the local vertical. This protocol can't separate that from the gyro's bias and g-sensitivity along gravity (see "The vertical channel"), so the two disc models make the same testable predictions. The tested flat model is the still disc, which is also how the flat model is usually stated. The spinning disc is still defined in the geometric truth generator (`analysis/tests/truthgen.py`), so anyone can check that claim.

### Sign conventions, checked

NED is right-handed (N × E = D), and a rotation vector ω turns a frame-fixed vector at `dr/dt = ω × r`.

- **Earth rate:** the spin axis is `cos φ` north and `sin φ` up, so the down component is `−sin φ`.
- **Moving north on the globe:** `ω_en = (0, −v/R, 0)`. Down then changes at `−(v/R) N`, so up tilts north, towards the direction of travel.
- **Moving east:** on the globe, local level tilts (north component `v/R`) and turns at `−v tan φ / R` about the vertical (meridian convergence). On the disc it only turns, at `−dλ/dt`.

**Independent check.** `analysis/tests/truthgen.py` computes `ω_in` from frame geometry alone. It builds the NED axes at each position in an inertial frame and differentiates their orientation numerically, with no transport or Earth-rate formula. All three tested models agree with it to 9 × 10⁻¹² rad/s (EVIDENCE §1). Synthetic test data takes its gyro truth from this generator, never from `lll.models`. The same formulas are implemented in Kotlin for the live display and checked against `docs/test_vectors.json`.

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
- **Horizontal Earth rate:** `h = |(w_0 − w_180)/2|`, after removing the part along up, taken from each 180° pair. Within a pair gravity sits on the same IMU axis, so g-sensitivity is identical and cancels. The Earth's horizontal component reverses. The globe predicts Ω|cos φ|; a still globe or the disc predicts 0. Noise biases a length upward, and a length isn't Gaussian near zero. As an approximate diagnostic, each face's length is treated as Rice-distributed, with σ per horizontal component. The reported rate is the maximum-likelihood length over both faces, with profile-likelihood 68 % and 95 % intervals (−2ΔlnL = 1, 3.84) that can reach zero. The p-value of zero rate comes from Σ r²/σ², χ² with 2 degrees of freedom per face. Any disagreement between the faces is added to σ.
- **Vertical:** `(w_0 + w_180)/2 · up`. This is the vertical Earth rate plus g-sensitivity along gravity, which can't be separated, and the result is marked as aliased.
- **IMU magnetic offset:** the mean magnetometer reading over the four positions is the field fixed in the IMU (hard iron), because the Earth's field cancels the same way.

### Reversal test (bench)

The IMU stays label up and is turned 180° about the vertical between placements, six pairs in all (`rev.up0.N`, `rev.up180.N`). Each pair gives `h_N = (w₀ − w₁₈₀)/2` with the part along up removed, free of g-sensitivity for the same reason as above.

The pairs are placed against the same edge, so their vectors point the same way. The horizontal rate is the length of their mean, estimated with the same Rice likelihood, with intervals and the p-value of zero rate. The scatter of the pair lengths is the unit's repeatability.

## In flight

### Segments and bins

The flight is cut into stable cruise segments, each at least 10 minutes long:

- speed above 100 m/s;
- |vertical speed| under 1.5 m/s;
- |turn rate| under 0.05 °/s;
- low vibration;
- a good GNSS fix, and a valid course: finite, within 3° by the receiver's own accuracy, and within 5° of the course computed from successive coordinates. A missing course is never filled in as north.

Segments also break at GNSS gaps, Bluetooth drops, bumps and deliberate IMU turns. Each segment is averaged into 60-s bins.

### The IMU's orientation

| quantity | source | uses the gyro? |
|---|---|---|
| model prediction `ω_in` (NED) | GNSS: latitude, height, north and east velocity | no |
| up axis | accelerometer | no |
| azimuth | GNSS course, plus a fitted crab offset per course leg | no |
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
- **Crab:** the IMU's orientation needs the fuselage heading, which in a crosswind differs from the GNSS course. Each course leg (segments within 10° of course share one) gets an offset δψ with a 5° Gaussian prior, so C_bn uses ψ_GNSS + δψ.
  - A nonlinear least-squares MAP solver minimizes the weighted residual sum of squares plus nuisance priors to convergence. The azimuth derivative maps a NED vector v to C_bn (v_E, −v_N, 0). Free, fixed-model and prior-sensitivity fits each minimize this objective.
  - For total angle d and local increment Δ, the prior penalty is `(d + Δ)² / σψ²`: the increment prior mean is **−d**. This same centering is used in bootstrap refits. The reported objective is evaluated at the final nonlinear parameters; the joint covariance uses the design linearized there. Bootstrap refits retain that local approximation.
  - Convergence diagnostics are exported; nonconverged fits are excluded from the primary corpus. Stopping uses relative cost/step tolerances 1e−10, gradient tolerance 1e−8 and at most 200 function evaluations.
  - It has no effect on the vertical-only fallback.
- **Each bin gives three rows**, or one in vertical-only mode. Weighted least squares fits the three k values and the nuisance terms.

Expected k for each model, in the order (k_rot, k_curv, k_disc): rotating globe (1, 1, 0), still globe (0, 1, 0), disc (0, 0, 1).

### Calibration vector covariance (0.6.0)

With regression design X and estimated per-visit axis covariance S, the coefficient covariance is
`Vθ = (XᵀX)⁺ ⊗ S` (coefficient-major order). S includes residual cross-axis covariance and a
nonnegative diagonal addition for the white-noise floor. Let A map the independent fitted position
coefficients to all four positions, with `w_down180 = −w_up0 −w_up180 −w_down0`. Each face has
horizontal projector `P_f = I − u_f u_fᵀ` and contrast `(w_f0 − w_f180)/2`. Stack those projected
contrasts into L. The exported six-vector covariance is `V_h = L (A ⊗ I) Vθ (Aᵀ ⊗ I) Lᵀ`, including
cross-face blocks. Covariance units are (degree/hour)², ordered up-x/y/z then down-x/y/z.

The existing Rice magnitude summary is explicitly an **approximate diagnostic**: it reduces each
projected covariance to half its trace and treats faces as independent, discarding anisotropy and
cross-face covariance. Its nominal intervals and p-values are not general anisotropic inference.
Ground population pooling remains disabled pending validation.

### Uncertainty and model tests

- **k intervals** are the larger of the analytic value and a moving-block bootstrap over bins. Bias wander correlates neighbouring bins.
- **χ²** is scaled by `(1 − ρ)/(1 + ρ)`, the effective-sample factor from the lag-1 autocorrelation of bin residuals within segments, per gyro axis, using the largest ρ.
- **Each model is tested against the free fit.** Fix its k values, refit the nuisance terms (crab included), and compare. `Δχ²` follows χ² with 3 degrees of freedom if that model is true. A model is **rejected at p < 0.0027, the nominal 3σ threshold**. Its true false-rejection rate is measured by simulation (`coverage.py --null`), not assumed (METHODOLOGY §10).
- **Bootstrap calibration.** For each model, simulate its null: its fitted values plus block-resampled residuals of the free fit, in blocks of up to 30 bins. Refit on the same design and compare the mean Δχ² with the degrees of freedom. If correlated noise inflates it, the observed Δχ² is divided by the inflation. The reported p is the larger of this and the autocorrelation-scaled one.
- **Systematic floor.** A floor of 0.02 is added in quadrature to the globe-rotation σ. It is calibrated by the coverage study (`analysis/tests/coverage.py`) under every hardware fault at once.
- Bootstrap ranges of Δχ² are reported. Relative likelihoods `exp(−Δχ²/2)` are shown, labelled as not probabilities.
- **Joint covariance.** `k_cov` is the analytic correlation of the three k (crab columns included), scaled to their final σ. Pooling uses it.
  The research harness exports empirical bootstrap covariance separately, including segment-restricted block sampling and block-length sweeps. It is not automatically substituted into production pooling.
- **Identifiability**, per term: the fraction of its predicted signal that the nuisance terms together could mimic, `sqrt(1 − |r|²/|x|²)`. Here r is the term's column after regressing out every nuisance column, with no priors: residual bias per gravity orientation, temperature and crab. Near 1 means only the nuisance priors constrain it. Above 0.95 for k_curv flags `k_not_identified`. The bias-only value is reported alongside.
- **Prior sensitivity.** Refit with the bias prior 3× wider, then the crab prior, then the temperature prior. If any k moves by more than 1σ under any of them, the flag is `prior_dominated`.
- **Crab sweep.** Refit with crab priors of 3°, 5°, 10° and 15°, and report k for each. If any k spans more than 1σ, the session is flagged `crab_sensitive`, for information only: the sweep doesn't detect crab bias (METHODOLOGY §16). A flight with one course leg is flagged `single_heading`.
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

The slip rate `δ̇` is the slope of the leftover angle in each segment. A segment is excluded when the slip exceeds 1.5 °/h and 3σ.

The watchdog runs twice. One version uses `D` and `s` from the World Magnetic Model, which is built on a globe. The other uses none, with `D` constant and `s = 1`, as a cross-check. A segment is left out of the gyro fit when the WMM version sees slip above 1.5 °/h and 3σ. Both results are reported.

The choice uses only the magnetometer and GPS, and the gyro fit itself never uses the magnetometer. A selection rule can still shift k, if what it drops correlates with the model terms. So whenever the WMM version excludes anything, the fit is repeated with no exclusions. If a model's rejection changes or any k moves by more than 1σ, the session is flagged `wmm_selection_sensitive` and left out of the primary result. The no-declination version alone would read the route's real declination change as slip.

## Pooling many sessions

Sessions with the same IMU share its quirks, so pooling is hierarchical, with random effects at each level. τ² comes from REML, and standard errors are modified Hartung–Knapp, with t intervals on n − 1 degrees of freedom:

```
sessions → per IMU unit → population of units
```

Each level adds the scatter between its members (τ²) to their error bars. The three k come from the same flights, so the model tests pool them jointly:

```
P_i = (C_i + diag τ²)⁻¹ over the terms session i identified,   V = (Σ P_i)⁻¹,   k̄ = V Σ P_i k_i
```

This runs within each unit, then across units, and V's diagonal is never below each term's own Hartung–Knapp variance. Each model's expected k is tested with `χ² = dᵀ V⁻¹ d`. With few units it is referred to F(p, df), using the smallest per-term df. A model is rejected at p < 0.0027 (nominal).

Only sessions that pass every gate enter the primary result:

- both calibrations;
- at least 60 minutes of cruise;
- curvature identified;
- not prior-dominated, not dependent on the WMM slip exclusion;
- an IMU unit rated qualified or usable by the latest bench result at or before the session;
- not synthetic.

Breakdowns by heading, mount, IMU variant and unit are consistency checks. Groups that disagree (heterogeneity p < 0.01) are flagged, never averaged away.

**Ground results across latitudes:**

- **Horizontal (primary):** `h = C |cos φ|`. A rotating globe gives C = 15.04, a still globe or the disc gives C = 0.
- **Vertical:** `up = A sin φ + B_unit`, with one intercept per IMU unit, because each unit's g-sensitivity along gravity is unknown. A is informed only by units calibrated at more than one latitude.

**Unit quality tiers** use instrument criteria only, never which model wins:

Horizontal repeatability comes from the reversal test when there is one, else from the palindrome calibration's σ. Allan deviation is also reported at 60, 900 and 1800 s. Its minimum is descriptive only, because it depends on run length and estimator. All thresholds are provisional until real units are measured ([BENCH.md](BENCH.md)).

| tier | requirement |
|---|---|
| qualified | Allan deviation at 300 s ≤ 3 °/h on the worst axis, and horizontal repeatability ≤ 2 °/h |
| usable | ≤ 6 °/h and ≤ 4 °/h, where measured |
| exploratory | anything else |

## Known approximations (please review)

- **Crab angle.** It is fitted per course leg (see "The fit"). On an eastbound leg it trades against the split between globe rotation and curvature, and an 8° crab still leaves about 2σ of bias (METHODOLOGY §16). The crab-prior sweep does not detect this bias; only heading diversity removes it.
- **Plumb line.** The accelerometer's plumb line includes small Coriolis and centripetal terms, about 0.2°. They are nearly constant in cruise.
- **Quantization.** At ±2000 °/s, one 16-bit count is 220 °/h. Noise dithers it, but coarse counts still interact with constant offsets at the °/h level (EVIDENCE §4). The app can select ±250 to ±2000 °/s, and the analysis decodes with the range the IMU reports back. A finer range risks clipping fast hand turns of the IMU; clipped turns are flagged, and the data after them is left out.
- **Temperature.** Chip temperature is reported by the IMU's firmware. A lag, or a nonlinear response, shows up as `temperature_sensitive`. Drift-run coefficients come from a fit with a time term. A monotonic warm-up, where temperature and time can't be told apart, is marked confounded and isn't used.
- **Device processing.** WitMotion firmware applies factory calibration and filtering before the data leaves the device (see FORMAT.md).
- **Vertical-channel limits.** See "The vertical channel" above.

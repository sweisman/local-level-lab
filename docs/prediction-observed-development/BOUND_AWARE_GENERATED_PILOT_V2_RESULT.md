# Bound-aware generated pilot: technical pass, physical miss

The [fresh frozen pilot](BOUND_AWARE_GENERATED_PILOT_V2_PLAN.md) closed
**2/2 technical tasks** in about 17 minutes, with no worker errors or active
locks. Both 26-parameter fits converged. The additional error-operator pass
produced the full bound-aware affine forecast artifact for each law.

| Generated IMU error law | Fitted path training horizontal RMS | Fitted path later horizontal RMS | Later truth inside affine intervals | Median interval span: north / east / up |
|---|---:|---:|---:|---:|
| Increment | 33.40 m | 108.60 m | 300/300 epochs, all coordinates | 108.5 / 102.1 / 22.5 m |
| Point | 29.80 m | 91.31 m | 300/300 epochs, all coordinates | 108.4 / 102.0 / 22.4 m |

Spans use the local WGS84 metric at the generated truth and approximate each
coordinate's physical width; they are not distance errors.

The original **10 m horizontal RMS physical screen fails in both cases**.
Technical completion does not relabel that result. The fits have active
calibration bounds: acceleration Z bias and gravity adjustment in the first
case, gyro X gain in the second. The bound-aware artifact retains all 26
columns and full affine rank; the ordinary unrestricted linear diagnostic
cannot support active bounds.

The intervals use the *correct assumed generated error law* and a local
affine model. They have a stated conditional 95% **marginal** construction,
but two covered paths do not measure its actual coverage. The calculation
does not establish simultaneous coverage over the whole path, bound the
nonlinear remainder, validate the observed-aircraft error law, or make an
Earth-model decision. The seven reserved ESA groups remain unopened.

This advances the software gate: bound-aware intervals can be constructed
without discarding calibration directions or hiding point-path failures.
The next step is an independently frozen generated cohort that tests complete
path coverage and physical adequacy separately, after the nonlinear and
observed-error assumptions are specified. The first short preflight's
[call-reserve failure](BOUND_AWARE_GENERATED_PILOT_V1_RESULT.md) remains
preserved.

[Machine-readable verified report](bounded-generated-pilot-v2-result.json) ·
[Earlier generated path audit](GENERATED_PATH_ERROR_AUDIT_RESULT.md) ·
[Later saved whole-forecast audit](GENERATED_SIMULTANEOUS_BOUND_RESULT.md)

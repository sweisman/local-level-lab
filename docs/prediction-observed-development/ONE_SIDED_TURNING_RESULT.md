# A new local stopping rule resolves the two generated turning fits

The [corrected finite study](ONE_SIDED_TURNING_V2_PLAN.md) completed both
technical tasks. The first study ID failed a path check before native work;
its two zero-native-call failures remain preserved. The corrected study
reconstructed the sealed generated noise, receiver positions, bounds, clock
and training operator, then fitted the original generating candidate from
the original zero start. It changed only the **versioned final numerical
stability check**.

| Generated case | New fit evaluations | New rule passed? | Original full-correction check passed? | New cost minus original cost |
| --- | ---: | --- | --- | ---: |
| Turning, level | 62 | Yes | **No** | 0 |
| Turning, shallow climb | 62 | Yes | **No** | 0 |

At both points, the repeated residual and Jacobian are exactly equal to the
baseline. None of the seven tested correction points lowers cost; their
largest physical-position differences are 0.000157 m and 0.0000814 m, below
the unchanged position limit. The original absolute cost-change check still
fails because its full linear correction raises actual cost slightly. The
new rule accepts no detectable cost-lowering move, stable predicted positions
and projected stationarity. Its [software controls](ONE_SIDED_STOPPING_PLAN.md)
also reject a known descent, unstable positions, nonstationarity and an
inconsistent repeat; exact and boundary optima pass.

The original two fits **remain nonconverged** under their frozen rule. This
new result only qualifies a local numerical method on two generated turning
cases. It does not establish a global optimum, accurate recovery of sensor
calibration, a calibrated aircraft error law or support for any Earth model.
The next gate is a matched generated comparison that applies this same rule
to every physical candidate and the straight/turning geometry cases, then
checks physical adequacy and withheld prediction. Observed-aircraft use and
the seven reserved ESA groups remain blocked.

The sealed corrected study is `data/generated-turning-one-sided-v2-20261117`.
It retains each full fit, both stopping-rule outcomes, source and input hashes,
charged work and recovery qualification. The failed setup is
`data/generated-one-sided-turning-v1-20261117`.

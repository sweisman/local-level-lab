# Bounded nonlinear scalar calibration controls

## Question and fixed region

Replace the preceding unbounded local projection with feasible nonlinear
calibration, without treating a finite optimization as a global certificate.
Preserve all completed evidence and the 53-stretch main result.

For every epoch, use one shared correction vector: three acceleration gains
±0.15, three offsets ±0.25 m/s², and gravity adjustment ±0.05 m/s². The residual
is the magnitude of (body minus offsets)/(1 plus gains), minus the magnitude
of the candidate force with the gravity adjustment subtracted from its down
component. These are assumed bounds, not measured device errors.

Use analytic derivatives for all seven coordinates. Optimize normalized bound
coordinates with SciPy trust-region reflective least squares; x_scale=1,
ftol=xtol=10⁻¹², internal gtol=2 times float64 machine epsilon, and maximum
200 residual evaluations. Count every residual
and Jacobian evaluation, including one fresh residual/Jacobian at the endpoint.
The hard combined allowance is 402 calls per start. Failure or budget exhaustion
remains an unfinished outcome; no retry or tolerance relaxation is allowed.

Fresh acceptance requires a successful solver status and projected-gradient
infinity norm at most 10⁻⁸. The projected gradient is x−clip(x−Jᵀr,−1,1) in
normalized bound coordinates. This is a numerical stationarity check, not
sensor accuracy, model adequacy or global optimality.

The internal scaled-gradient rule is deliberately near machine precision because
it can otherwise terminate before the fresh projected-gradient check passes
at exact boundaries. A positive internal tolerance still permits termination
at zero residual in rank-deficient controls. The fresh acceptance limit, bounds
and evaluation allowance remain independent of this internal numerical guard.

## Qualification gate

First use four known-answer mathematical fixtures with 121 epochs: an excited
interior solution, near-boundary solution, exact-boundary solution, and a
rank-deficient constant-force solution. Their measured forces are constructed
independently from declared proper rotations and planted calibrations.

Each uses three fixed starts: zero, the alternating vector
(0.8,−0.8,0.8,0.8,−0.8,0.8,0.8), and its negative. All twelve must pass fresh
stationarity, recover residual RMS at most 10⁻⁷ m/s², and agree in residual
history within 10⁻⁷ m/s² RMS. Do not require unique calibration parameters when
force magnitudes do not identify them. A failed gate blocks the trajectory matrix.

## Matched matrix after qualification only

Read the 72 sealed constructed histories from the preceding local-calibration
study, checking source receipt and artifact hashes before use. They are exact
software fixtures, not original airborne measurements. Fit each from the same
three fixed starts, retaining all candidates and failures.

For each identity report physical residuals, endpoint, stationarity, active
bounds, all calls and the three-start residual agreement. Repeat agreement
requires every start to pass, RMS scores within 10⁻⁸ m/s² and residual histories
within 10⁻⁷ m/s² RMS. There is no required wrong-model separation. Failure of
repeatability prevents promoting this diagnostic into recorded-data fitting.

## Finite limits

| Resource | Ceiling |
|---|---:|
| Qualification starts | 12 |
| Matched matrix starts | 216, only after qualification |
| Total mathematical optimizer starts | 228 |
| Residual plus Jacobian calls | 91,656 (402 per start) |
| Observed starts / native integrations / original-file reads | 0 / 0 / 0 |
| Numerical threads | Four total, one worker |
| Wall time | 300 seconds |
| Retries | Zero |

Freeze sources, environment, fixture hashes, all task identities and allowances
before launch. Charge each start before execution, preserve interruption charges,
and never restart completed work. Publication reads saved results only. Passing
software controls does not establish a real-recording noise model or authorize
an observed-data campaign. Quantization, timing and uncertainty gates remain.

# Comparing two wind corrections

The experimental physical wind/airspeed correction is implemented. It describes wind and
aircraft movement through the air separately, then checks whether their combination agrees
with GPS ground motion. The earlier wind correction instead allows slowly changing sideways
pointing coefficients. Neither has established reliable decisions for real IMU recordings.

The next comparison should use the same simulated recordings for both corrections, including
wind alone, wind with mixed IMU drift, and wind with drift, correlated noise and temperature.
The independent wind-truth generator remains unchanged. Retain all exclusions, fit failures,
model-pair information, prior sensitivity, bound hits and runtime; do not select only successful
fits. A smaller nuisance space is useful only if it still covers plausible errors.

`proposal.json` is a preparation-only manifest for a Frankfurt–Johannesburg development
window with simulated frequent GPS along the assumed short-interval path. It proposes three
paired seeds, three Earth truths, three nuisance scenarios and two corrections: 27 simulated
recordings evaluated 54 times. IMU turns at 20, 40 and 60 minutes pass the revised
two-minute-buffered maneuver mask on that assumed route; the schedule is not optimized.
Its timing checks are geometry checks on an assumed path, not
verification of aircraft motion between public fixes or reconstructed IMU orientation.
Bootstrap is zero, so this comparison cannot establish rare error rates. Runtime is unmeasured.

**Authorized executions: zero.** The manifest is not run permission. Obtain a bounded timing
and diagnostic-storage budget before execution. There is no final calibration or validation
policy. Older proposals remain historical for their frozen sources.

The refreshed `optimizer-estimate.json` retains ten permitted grid times and an upper bound
of 5,571,423 SVD calculations for a three-turn, beam-16 search with both wind corrections.
No search or SVD scoring was executed. This bound explains why search needs a separate budget.

Software verification completed with **336 tests passed in 4 minutes 42 seconds**.
The server's async upload test stalls inside the execution sandbox; the complete suite passed
outside it with a ten-minute process deadline and two numerical threads. One dependency
deprecation warning was reported. Tests do not establish flight-domain power or error tails.

The physical candidate requires `--crab-model wind_tas --design-mode envelope` in
`analysis/tests/research.py`; it can be compared with `wind` in the same invocation. Requested
bootstrap also requires `--bootstrap-refit nonlinear`. Geometry search accepts `wind_tas`
among the worst-case nuisance candidates. Physical priors and bounds are frozen in
`analysis/lll/wind_tas.py`; changing them requires a new policy/source freeze.

GPS alone supplies no independent aircraft heading or airspeed observation. The physical
constraint is conditional on the recorded ground vectors, and its gyro bootstrap holds them
fixed. Unknown public-track errors remain a separate limitation. The finite design envelope
checks stated nuisance examples, not every wind trajectory. See the
[technical validation record](../VALIDATION_TECHNICAL.md) for the numerical assumptions.

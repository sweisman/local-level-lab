# Generated forecasts for two different targets

The [frozen two-case pilot](DUAL_TARGET_GENERATED_PILOT_PLAN.md) finished all
2/2 tasks. Both fits converged. Each saved a forecast range for the aircraft's
physical position and a separate range for what a noisy receiver would report.
Both ranges were saved before the later generated data were opened.

| Generated IMU error law | Raw fitted path: later horizontal RMS | Later receiver data vs fitted receiver-target center | Mean full horizontal receiver range | Receiver coordinates within range |
|---|---:|---:|---:|---:|
| Independent increments | 242.7 m | 18.3 m | 208.0 m | 900/900 |
| Sampled rate points | 245.4 m | 30.1 m | 207.8 m | 900/900 |

Horizontal range width is the diagonal of the north/east coordinate box,
averaged over the 300 later seconds.

The two point-error columns describe **different predictions**. The raw path
is scored against the noise-free physical route. The receiver-target center
uses earlier receiver observations to predict later noisy receiver reports.
It is smaller partly because earlier observations constrain shared error
states. Neither raw path passes the old 0.1 m clean-data accuracy rule; the
[noise-floor audit](GENERATED_NOISE_FLOOR_AUDIT_RESULT.md) had already shown
that rule is unsuitable for these noisy inputs.

All later physical coordinates also fall within their saved physical-position
ranges. That is a descriptive result for two generated cases on one route. The
receiver ranges are broad relative to the center errors, and the study fits
only one candidate Earth model. It therefore establishes the **two-target
software path**, not calibrated coverage, a useful three-model decision, or
performance on an aircraft. The separate short preflight passed its wiring
gate but its deliberately short fit did not converge.

The [machine-readable verified report](dual-target-full-result.json) binds
the study completion, source, scorer and plan hashes. The
[preflight report](dual-target-preflight-result.json) and retained study
artifacts preserve the earlier-prefix check and all charged work. The next
study must use new routes and noise draws, predeclare a useful-width rule, and
count every failed fit or interval in its coverage denominator. Observed
aircraft error assumptions remain to be established.

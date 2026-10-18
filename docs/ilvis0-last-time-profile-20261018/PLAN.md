# Final-stretch zero-field timing profiles

The specified-field endpoint study is complete: all six checks passed in 100
native calls, including both processing-case primary/repeat pairs. The final
stretch `b4e44ddc0f130ecd45674c78` still has different zero-field-globe time
alignments: its saved repeat is at the +0.15 s physical bound, about 57 ms from
the primary. Their costs differ beyond the required repeat tolerance.

Hold each of the two exact saved offsets fixed, separately under unsubtracted
and profiled-removal assumptions. At every offset, fit every other active
parameter twice: once from the original primary and once from the original
repeat. Both original starts and both offsets remain represented regardless
of which fits better. Passing source repeats are diagnostic inputs, not
automatic qualification of the other endpoint.

Use the existing fixed-time adapter and bounded trust solver unchanged. Removing
the time column here defines a conditional diagnostic; it does not fix timing
in the final scientific comparison. Keep the raw observations, receiver weights,
clock, physical bounds and processing hypotheses fixed. No instrument drift
model, extra calibration freedom or favorable interval selection is introduced.

## Qualification and freeze

One 26-test software batch, at most 120 seconds and 1,024 callbacks: the existing
15 fixed-time adapter checks, including three compiled-motion controls, and
eleven scope/worker checks. Tests cover parameter lifting/reduction, exact-bound
timing anchors, both processing cases, both nuisance starts, unrelated model
exclusion, failure propagation and private-template isolation. No archive
originals or observed fits occur during qualification.

Require the completed field-endpoint evidence before preparing the observed
freeze. Seal its completion and receipts alongside the exact source endpoints,
selected intervals, original hashes, qualified sources, kernels and numerical
environment. Preserve every prior study and failure. The worker privately adapts
the completed executor; it does not edit or resume it.

## Finite observed allowance

| Item | Maximum |
|---|---:|
| Fresh smooth controls | 2 × 3 native calls |
| Conditional nuisance fits | 8 × 80 fitting calls |
| Final full-Jacobian diagnostics | 8 × 1 native call |
| Total charged identities | **10** |
| Conditional optimizer starts | **8** |
| Total native calls | **654** |
| Saved within-anchor comparisons | 4 |
| Total numerical threads | 4, one worker |
| Retries | 0 |

At the preceding matched study's 32 seconds per native call, exhausting this
ceiling would take about 5.8 hours. Earlier conditional profiles stopped well
below their ceilings; that does not authorize increasing this one. Charge before
execution, require fresh controls first, preserve failed starts and block any
incomplete receipt transaction. Never restart completed or charged identities,
reset counters or reuse an earlier allowance.

At each fixed offset, require both conditional fits and compare their costs and
tracks using the existing relative-cost limit 10^-6 and 0.01 m per-axis RMS limit.
Save the complete full-parameter residual/Jacobian, receiver epochs and timing
derivative for each final diagnostic, including failures.

Report every result. Fixed-time completion does not establish free-time
stationarity, repeat agreement across different offsets or a global optimum.
The next full free-time test requires its own finite freeze, followed by all
model/case companions and scheduled repeat checks. Published findings remain
**52 globe / 0 flat / 1 unresolved** throughout this conditional study.

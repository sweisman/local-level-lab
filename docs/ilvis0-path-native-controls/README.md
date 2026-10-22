# Native packet adapter comparison

**6/6 generated controls pass.**

| Model | Processing | Result | Position gap | First-derivative gap |
|---|---|---|---:|---:|
| Globe + field | Zero removal | Pass | 3.95e-10 m | 2.76e-14 m |
| Globe + field | Profiled removal | Pass | 3.95e-10 m | 2.18e-14 m |
| Globe, zero field | Zero removal | Pass | 5.65e-10 m | 1.38e-14 m |
| Globe, zero field | Profiled removal | Pass | 5.66e-10 m | 1.59e-14 m |
| Flat disc | Zero removal | Pass | 5.69e-10 m | 1.62e-14 m |
| Flat disc | Profiled removal | Pass | 5.69e-10 m | 9.04e-15 m |

Each case checks the same generated first packet and all 27 physical parameter directions. The one-micrometre tolerance compares software values and first derivatives, not sensor accuracy. No aircraft fits or original recordings are read.

The first-order native reference does not independently verify second or third derivatives; those retain separate known-answer checks. These controls do not qualify full-history prediction ranges, complete clock/rotation branches, native execution-error bounds or an observational error law.

[Frozen limits](PLAN.md) · [Trajectory components](../ilvis0-path-motion/README.md) · [Remaining prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).

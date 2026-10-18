# Why the last free-timing fits failed

The full trial passed both controls but failed all four target checks. Repeated target solutions agree closely; that alone does not establish local stability. This audit uses saved Jacobians, fit histories and receiver timing only: **zero native predictions, zero observed fits and zero original-recording reads**.

| Processing case / start | Accepted / rejected steps | Full timing correction | Nearest clock transition | Full / fixed-time affine change |
|---|---:|---:|---:|---:|
| bias1_unsubtracted / primary | 0 / 39 | +0.0528699 s | +1.82572e-09 s | -0.0292658 / -1.36424e-11 |
| bias1_unsubtracted / repeat | 0 / 39 | +0.0528701 s | +1.82572e-09 s | -0.0292658 / -1.06456e-09 |
| bias1_profiled_removal / primary | 0 / 39 | +0.0528699 s | +1.9602e-10 s | -0.0292658 / -1.43245e-11 |
| bias1_profiled_removal / repeat | 0 / 39 | +0.0528701 s | +1.9602e-10 s | -0.0292658 / -9.69294e-10 |

Signed affine changes compare each local correction with the feasible zero step. A negative value predicts a decrease in the linear approximation; it is not a fresh full-model result. The report retains the corrections, spectra, packet-state changes and the preceding native trial's actual increases. Fixing timing is diagnostic only.

No fit label, physical bound or stopping limit changes. Findings remain **52 globe / 0 flat / 1 unresolved**.

[Finite plan](PLAN.md) · [Full trial](../ilvis0-last-free-time-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).

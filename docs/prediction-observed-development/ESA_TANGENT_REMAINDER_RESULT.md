# How far the linear forecast follows a calibration change

On ESA recording 187, the scalar integrator reproduced the sealed nominal
forecast within one nanometre. It then propagated six finite changes along
the three calibration combinations least constrained by the earlier fit.
All changes stayed inside the original bounds. The fitted onboard-removal
parameter started at its lower bound, so the checks moved inward.

| Weak direction | Step in normalized calibration coordinates | Earlier RMS error in the linear approximation | Later RMS error in the linear approximation | Later error as a share of displacement |
|---|---:|---:|---:|---:|
| 1 | 0.01 | 0.0015 mm | 0.0063 mm | 0.018% |
| 2 | 0.01 | 0.072 mm | 0.257 mm | 0.64% |
| 3 | 0.01 | 0.066 mm | 0.199 mm | 0.37% |
| 1 | 0.10 | 0.148 mm | 0.634 mm | 0.18% |
| 2 | 0.10 | 7.22 mm | 25.7 mm | 6.5% |
| 3 | 0.10 | 6.56 mm | 19.9 mm | 3.7% |

Increasing the step tenfold increased the error by about a factor of 100
on each ray. At the larger step, the largest single-query error was 34.2 mm.
The step sizes use the normalized fit coordinates. They describe how far the
calculation moved within the fit's permitted range, without assigning a
probability to that move.

This checks one saved fit and three individual directions. Combining
calibration changes can produce different errors. An aircraft decision still
needs a bound across the feasible earlier-fit region for every model and a
supported law for forecast errors that also change over time.

One of one tasks passed. There were seven value sweeps, zero new fits and
zero reads of withheld receiver positions or reserved flights.

[Fixed study plan](ESA_TANGENT_REMAINDER_PLAN.md) ·
[Original tangent replay](ESA_NATIVE_TANGENT_REPLAY_RESULT.md)

The closed study ID is `esa-tangent-remainder-v1-20261118`. Its manifest
SHA-256 is `ea8916a3dc0229d7001f0db42bc1a3f37f470df81d57746f3b32a34757331e62`.
The sealed `finite-changes.json` stores all six signed displacement paths,
their actual parameter steps and the RMS and maximum errors. Its SHA-256 is
`b710c4df6c6a68eba85510d07f08ae9cffc009b51eba87b7ed24db7b315d1c83`.

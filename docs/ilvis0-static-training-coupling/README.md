# Calibration relationships tighten the bound modestly

**All 54 static checks pass.** The complete eight-part orientation covers
reduce the reference-acceleration allowance by 3.7–7.1% across the six cases.
This is useful progress in the bounding method; it does not establish useful
long-record prediction ranges.

These are generated software cases, not new aircraft analyses. The allowance
describes how much the reference acceleration may change across the permitted
calibration set. It is neither measured aircraft acceleration nor sensor noise.

| Candidate | Recorded-field removal assumption | Previous allowance | Full-domain coupling | Complete yaw cover |
|---|---|---:|---:|---:|
| Globe, specified field | None | 1.703399 | 1.696078 | 1.639915 |
| Globe, specified field | Profiled | 1.728696 | 1.721266 | 1.664612 |
| Globe, zero field | None | 1.381232 | 1.373437 | 1.314952 |
| Globe, zero field | Profiled | 1.388155 | 1.380314 | 1.321660 |
| Flat disc | None | 0.871332 | 0.863822 | 0.809254 |
| Flat disc | Profiled | 0.952857 | 0.945220 | 0.890000 |

All acceleration allowances are in m/s². Each cover value is the worst
of all eight fixed yaw parts. No part was dropped. All 51 coordinates and
all 30 original training inequalities were retained, with 48 checked coupling
constraints added in every calculation. The physical bounds stayed fixed.

The comparison took 4.85 minutes on one numerical thread.
It used 3,240 linear-program proposals and 9,720 exact support reservations;
all indexed journals, source hashes and sealed results were verified.
There were no trajectory integrations, aircraft reads or optimizer starts.

The next step is to trace the larger position-reconstruction allowance to
its remaining terms before another expensive full-history calculation.
Whole-domain numerical qualification, the complete prediction period and
the aircraft error model remain separate requirements. The main 53-stretch
findings are unchanged.

[Method and finite limits](PLAN.md) ·
[Original prediction failures](../ilvis0-long-staged-feasibility-v2/README.md) ·
[Shared implementation](../../analysis/lll/ilvis0_coupled_prediction.py) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Reproduce the evidence](../REPRODUCIBILITY.md).

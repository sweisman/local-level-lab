# Complete-vector path between saved aircraft fits

Six fixed calibration vectors finished without refitting. Each vector
is one quarter, one half or three quarters of the way between two
saved solutions. Only the training receiver positions were scored.
The later forecasts were compared with each other, never with later
receiver positions. Costs are weighted squared errors, not metres.

## 2010 northern pair

Endpoint training costs: 0.033167 and 0.033326. Their later forecasts differ by up to 0.752 m.

| Fraction from A | Training cost | Above worse endpoint | Later path gap to A | Later path gap to B |
|---:|---:|---:|---:|---:|
| 25% | 0.034282 | 0.000956 | 0.195 m | 0.762 m |
| 50% | 0.035160 | 0.001835 | 0.297 m | 0.660 m |
| 75% | 0.034358 | 0.001033 | 0.437 m | 0.410 m |

## 2015 southern pair

Endpoint training costs: 0.736341 and 0.736554. Their later forecasts differ by up to 0.320 m.

| Fraction from A | Training cost | Above worse endpoint | Later path gap to A | Later path gap to B |
|---:|---:|---:|---:|---:|
| 25% | 0.736361 | -0.000194 | 0.082 m | 0.240 m |
| 50% | 0.736417 | -0.000137 | 0.162 m | 0.160 m |
| 75% | 0.736474 | -0.000080 | 0.241 m | 0.080 m |

The northern straight-line connection has a modest training-cost
rise near its middle. All three sampled southern interior costs fall
between the two endpoint costs while the later path moves across the
0.320 m endpoint spread. These are paths through parameter space, not new
optimized solutions; a different curved route could behave differently.
This diagnostic cannot establish a global optimum, forecast accuracy,
physical adequacy or an Earth-model decision. All earlier failed
numerical stopping labels remain unchanged.

[Complete data table](observed-pair-path.csv) · [Frozen plan](OBSERVED_PAIR_PATH_PLAN.md) · [Calibration-swap study](OBSERVED_CALIBRATION_SWAP_RESULT.md)

# ESA: predicting the later flight

**15/24 starts supplied qualified fits and complete forecasts; 1/4 matched comparisons are complete.**

Every setting needs qualified predictions from all three candidates. A
missing fit leaves that comparison unresolved; it does not support either
geometry. The tables retain every start and physical-accuracy failure.

The one selected interval lasts 20.0 minutes, averages 292.2 km/h near 64.19° N, and contains 360,029 original IMU samples.
An IMU is an inertial measurement unit containing gyroscopes and accelerometers.
Earlier 800 receiver positions train calibration; later 400 check a
continuous IMU forecast. They do not adjust its calibration or path.

| Working errors | Removal case | Candidate | Selected start | Later horizontal RMS | Later height RMS | Prediction accuracy |
|---|---|---|---:|---:|---:|---|
| Short memory | Zero | Globe + specified field | 0 | 26.92 m | 211.901 m | Failed |
| Persistent | Zero | Globe + specified field | 0 | 21.0445 m | 168.229 m | Failed |
| Short memory | Profiled | Globe + specified field | 1 | 26.9201 m | 211.901 m | Failed |
| Persistent | Profiled | Globe + specified field | 0 | 21.0445 m | 168.229 m | Failed |
| Short memory | Zero | Globe + zero field | 0 | 4268.55 m | 1341.77 m | Failed |
| Persistent | Zero | Globe + zero field | 0 | 3742.52 m | 834.655 m | Failed |
| Short memory | Profiled | Globe + zero field | 1 | 4268.54 m | 1341.78 m | Failed |
| Persistent | Profiled | Globe + zero field | 0 | 3742.53 m | 834.653 m | Failed |
| Short memory | Zero | Tested disc | 1 | 8442.52 m | 2016.18 m | Failed |
| Persistent | Zero | Tested disc | — | Unavailable | Unavailable | No qualified training fit |
| Short memory | Profiled | Tested disc | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Profiled | Tested disc | — | Unavailable | Unavailable | No qualified training fit |

RMS describes a typical error size. Height matters alongside horizontal
position. Selection uses converged training cost alone, even when another
start has a smaller later error. If the selected training fit cannot
produce a complete forecast, the comparison retains that failure rather
than switching starts. Both starts remain in the full CSV.

| Working errors | Removal case | Lower-error shape family | Preferred model passes training and prediction accuracy | Field comparison |
|---|---|---|---|---|
| Short memory | Zero | Globe | No | Not assessed |
| Persistent | Zero | Incomplete numerical comparison | Unavailable | Not assessed |
| Short memory | Profiled | Incomplete numerical comparison | Unavailable | Not assessed |
| Persistent | Profiled | Incomplete numerical comparison | Unavailable | Not assessed |

These are descriptive comparisons of later total three-dimensional RMS,
not calibrated likelihood tests. The shape stage compares the better globe
candidate with the disc. Field ranking follows only a complete globe
preference whose selected model passes physical accuracy in both sections.

Accuracy requires horizontal RMS ≤10 m, height RMS ≤30 m, maximum horizontal
error ≤50 m and maximum absolute height error ≤150 m. A preferred but inaccurate
model is not an adequate flight reconstruction. Numerical convergence, physical
accuracy and calibrated confidence are separate.

The run used 1,524 native calculations in 2.32 hours.
The saved-data audit verifies source and input hashes, exact earlier/later
boundaries, every calibration column, repeated source inputs, compiled kernels,
physical errors and all charges. It performs no fit or propagation.

The 24 starts and four matched settings reuse one development recording.
They are not independent replications. Both receiver-error cases are working
assumptions; rate sampling and upstream processing remain explicitly modeled
assumptions. No confidence level, field cause or solar-versus-sidereal rate
distinction is established here. Seven confirmation groups stay protected,
and the original NASA findings remain unchanged.

[Every start and its errors](fits.csv) · [Matched comparisons](comparisons.csv) · [Frozen fitting plan](FIT_PLAN.md) · [Prepared interval](../esa-development-pilot-preparation/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)

# ESA: wider-precision prediction

The original measurements, earlier/later split, height-gravity law,
calibration bounds, starts, stopping checks and accuracy limits are unchanged.
Only the explicitly qualified numerical calculation uses wider precision.
Every failed fit remains visible; earlier failed results are not relabeled.

**22/24 starts supplied qualified fits and complete forecasts; 3/4 matched comparisons are complete.**

Every setting needs qualified predictions from all three candidates. A
missing fit leaves that comparison unresolved; it does not support either
geometry. The tables retain every start and physical-accuracy failure.

The one selected interval lasts 20.0 minutes, averages 292.2 km/h near 64.19° N, and contains 360,029 original IMU samples.
An IMU is an inertial measurement unit containing gyroscopes and accelerometers.
Earlier 800 receiver positions train calibration; later 400 check a
continuous IMU forecast. They do not adjust its calibration or path.

| Working errors | Removal case | Candidate | Selected start | Later horizontal RMS | Later height RMS | Prediction accuracy |
|---|---|---|---:|---:|---:|---|
| Short memory | Zero | Globe + specified field | 1 | 7.80272 m | 13.3726 m | Passed |
| Persistent | Zero | Globe + specified field | 0 | 6.79528 m | 13.7126 m | Passed |
| Short memory | Profiled | Globe + specified field | 0 | 7.80273 m | 13.3726 m | Passed |
| Persistent | Profiled | Globe + specified field | 1 | 6.79528 m | 13.7126 m | Passed |
| Short memory | Zero | Globe + zero field | 1 | 4267.5 m | 1230 m | Failed |
| Persistent | Zero | Globe + zero field | 0 | 3708.69 m | 671.147 m | Failed |
| Short memory | Profiled | Globe + zero field | 1 | 4267.5 m | 1230 m | Failed |
| Persistent | Profiled | Globe + zero field | 0 | 3708.69 m | 671.147 m | Failed |
| Short memory | Zero | Tested disc | 1 | 8407.03 m | 1906.54 m | Failed |
| Persistent | Zero | Tested disc | 0 | 7361.1 m | 782.09 m | Failed |
| Short memory | Profiled | Tested disc | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Profiled | Tested disc | 1 | 7361.1 m | 782.089 m | Failed |

RMS describes a typical error size. Height matters alongside horizontal
position. Selection uses converged training cost alone, even when another
start has a smaller later error. If the selected training fit cannot
produce a complete forecast, the comparison retains that failure rather
than switching starts. Both starts remain in the full CSV.

| Working errors | Removal case | Lower-error shape family | Preferred model passes training and prediction accuracy | Field comparison |
|---|---|---|---|---|
| Short memory | Zero | Globe | Yes | Specified field has lower error |
| Persistent | Zero | Globe | Yes | Specified field has lower error |
| Short memory | Profiled | Incomplete numerical comparison | Unavailable | Not assessed |
| Persistent | Profiled | Globe | Yes | Specified field has lower error |

These are descriptive comparisons of later total three-dimensional RMS,
not calibrated likelihood tests. The shape stage compares the better globe
candidate with the disc. Field ranking follows only a complete globe
preference whose selected model passes physical accuracy in both sections.

Accuracy requires horizontal RMS ≤10 m, height RMS ≤30 m, maximum horizontal
error ≤50 m and maximum absolute height error ≤150 m. A preferred but inaccurate
model is not an adequate flight reconstruction. Numerical convergence, physical
accuracy and calibrated confidence are separate.

The run used 1,175 native calculations in 8.01 hours.
The saved-data audit verifies source and input hashes, exact earlier/later
boundaries, every calibration column, repeated source inputs, compiled kernels,
physical errors and all charges. It performs no fit or propagation.

The 24 starts and four matched settings reuse one development recording.
They are not independent replications. Both receiver-error cases are working
assumptions; rate sampling and upstream processing remain explicitly modeled
assumptions. No confidence level, field cause or solar-versus-sidereal rate
distinction is established here. Seven confirmation groups stay protected,
and the original NASA findings remain unchanged.

[Every start and its errors](fits.csv) · [Matched comparisons](comparisons.csv) · [Frozen fitting plan](PLAN.md) · [Prepared interval](../esa-development-pilot-preparation/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)

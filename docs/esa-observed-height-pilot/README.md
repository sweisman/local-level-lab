# ESA: height-dependent gravity prediction

The original twenty-minute recording, earlier/later split, calibration bounds,
starts, receiver-error policies and accuracy limits are unchanged. This run
changes only the declared gravity law: gravity varies with the predicted
height, anchored to the first earlier receiver height. Later receiver heights
are opened only after the complete forecast has been saved.

[Original pilot](../esa-development-pilot/README.md) · [Matched changes for every start](baseline-changes.csv).

**8/24 starts supplied qualified fits and complete forecasts; 1/4 matched comparisons are complete.**

Every setting needs qualified predictions from all three candidates. A
missing fit leaves that comparison unresolved; it does not support either
geometry. The tables retain every start and physical-accuracy failure.

The one selected interval lasts 20.0 minutes, averages 292.2 km/h near 64.19° N, and contains 360,029 original IMU samples.
An IMU is an inertial measurement unit containing gyroscopes and accelerometers.
Earlier 800 receiver positions train calibration; later 400 check a
continuous IMU forecast. They do not adjust its calibration or path.

| Working errors | Removal case | Candidate | Selected start | Later horizontal RMS | Later height RMS | Prediction accuracy |
|---|---|---|---:|---:|---:|---|
| Short memory | Zero | Globe + specified field | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Zero | Globe + specified field | 0 | 6.79528 m | 13.7126 m | Passed |
| Short memory | Profiled | Globe + specified field | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Profiled | Globe + specified field | — | Unavailable | Unavailable | No qualified training fit |
| Short memory | Zero | Globe + zero field | 0 | 4267.48 m | 1229.99 m | Failed |
| Persistent | Zero | Globe + zero field | 0 | 3708.69 m | 671.146 m | Failed |
| Short memory | Profiled | Globe + zero field | 1 | 4267.5 m | 1230 m | Failed |
| Persistent | Profiled | Globe + zero field | 1 | 3708.69 m | 671.146 m | Failed |
| Short memory | Zero | Tested disc | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Zero | Tested disc | 0 | 7361.1 m | 782.084 m | Failed |
| Short memory | Profiled | Tested disc | — | Unavailable | Unavailable | No qualified training fit |
| Persistent | Profiled | Tested disc | 1 | 7361.1 m | 782.088 m | Failed |

RMS describes a typical error size. Height matters alongside horizontal
position. Selection uses converged training cost alone, even when another
start has a smaller later error. If the selected training fit cannot
produce a complete forecast, the comparison retains that failure rather
than switching starts. Both starts remain in the full CSV.

| Working errors | Removal case | Lower-error shape family | Preferred model passes training and prediction accuracy | Field comparison |
|---|---|---|---|---|
| Short memory | Zero | Incomplete numerical comparison | Unavailable | Not assessed |
| Persistent | Zero | Globe | Yes | Specified field has lower error |
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

The run used 1,478 native calculations in 2.22 hours.
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

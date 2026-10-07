# Full-pipeline replay: useful partial geometry, weak statistical separation

All six authorized analyses completed and converged. This is progress beyond a design
calculation: the pipeline recovered orientation from simulated measurements and retained
useful partial model comparisons under both wind treatments. It still does not establish
a strong or validated Earth-model result.

The fixed Chicago–Los Angeles window and IMU turns were analyzed under each of the three
physical-model truths, with both wind candidates and combined wind plus mixed IMU drift.
One shared development seed makes the candidates matched. The saved inputs to the fitter
were independently checked identical between candidates for each truth, across all 23
stored input fields. Frozen source, input and numerical-environment identities match.

The run took 335.20 seconds, about 5.6 minutes, using at most two workers with one numerical
thread each. The six attempt times sum to 376.53 seconds; that is not the wall time.
There were no processing failures or unknown runtimes. All six attempts are now spent.

Each analysis retained 99 cruise minutes, adequate heading diversity and six mount epochs.
Reported forward-axis uncertainty ranged from 0.392° to 0.572°, with the provisional
matched-reference method. The magnetic watchdog excluded no segments. Real coverage of
the orientation uncertainty remains unvalidated. Global model-test rank was one throughout.

| Comparison | Passed pairwise eligibility | Decisions |
|---|---:|---|
| Rotating versus stationary globe | 6 of 6 | All abstained |
| Stationary globe versus disc | 6 of 6 | All abstained |
| Rotating globe versus disc | 0 of 6 | All abstained |

The complete three-model gate still excludes every analysis because one contrast is not
identified. Pairwise eligibility is conditional on the retained bins and recovered axes.
The earlier nominal design screen used supplied axes and a fixed 5° orientation uncertainty;
it is a different calculation and failed the broader wind candidate. The narrower recovered
uncertainty and retained measurement geometry here must not be substituted into that older
planning result or treated as unconditional protocol guarantees.

No bootstrap samples or empirical thresholds were requested in this processing pilot.
Thus every pair abstains, including those with usable geometry. There is no calibrated
winner, false-rejection bound or power estimate. A pair coordinate is not a three-model
decision, especially for a generating truth outside that pair.

## Why the planning calculation looked stronger

An audit of the saved analysis outputs found residual-based gyro scales of about 38.3°/hour.
The design grid assumed 3 or 6°/hour. These residual scales include simulated sensor effects,
processing error and possible model mismatch; they are not measurements of actual WT901
performance. A subsequent saved-data decomposition identifies the dominant cause below.

For the stationary-globe/disc comparison, the fixed-noise design reports information values
of about 27–41, whereas the free-fit calculation with observed residual weights reports
about 0.52–1.36. The states, weights and conditioning differ, so this is a diagnostic
comparison rather than a simple correction factor. The nonlinear profile's standard
error is about 0.62–0.64 on a coordinate where the two endpoints are one unit apart.
That leaves substantial overlap even though the geometry retains the contrast.

## The dominant loss comes from motion correction

The accelerometer measures gravity together with the effect of aircraft acceleration.
The analysis currently treats its direction as the gravity direction. When acceleration
changes, that apparent direction can move even if the IMU does not tilt. Subtracting its
rate of change therefore introduces a false gyro correction.

An independent reconstruction of the prescribed replay attitude, using only saved inputs
and parameters, found the following. No flight was generated and no optimizer was run.

| Saved-data diagnostic | Rate, degrees/hour |
|---|---:|
| Final fitted residual RMS, over all three sensor axes | 39.23–39.29 |
| Aircraft-motion correction mismatch | About39.63 |
| Sensor effects and calibration error after subtracting prescribed motion and science | About3.9 |
| False tilt correction caused by apparent gravity | About38.12 |
| Residual after substituting prescribed true gravity, without refitting | About12 |

The earlier38.3°/hour weighting scale comes from a preliminary fit; it is frozen before the
final fit and is a different quantity from the final residual RMS. The reconstructed
accelerometer direction agrees with the stored direction within0.0035°, but apparent and
true gravity differ by up to2.52°. The prescribed aircraft-roll contribution is only
8.41°/hour RMS and does not explain the dominant correction error. Fitted science/orientation
discrepancy is about1.1°/hour. Components are correlated; their squared rates must not be
added as independent variances. The full decomposition closes to numerical precision.

True gravity here comes from simulator attitude, which is unavailable in an actual recording.
Its substitution is a diagnostic, not an operational fix or new Earth-model result. It also
leaves a material motion discrepancy. The next work is an acceleration-aware motion and
orientation treatment using observed position and IMU data, including uncertainty from
position derivatives, gaps, wind and orientation. It must preserve the frozen replay and
must not use simulator truth to make real-flight decisions. Independent physical fixtures
already demonstrate that acceleration alone can produce the false tilt correction.

It is premature to launch a large calibration campaign merely because the geometry gate
passes. Hardware characterization, realistic uncertainty, justified wind assumptions and
separately frozen calibration and independent validation remain necessary.

`review.json` preserves fit, geometry, orientation, profile and runtime summaries;
`noise-review.json` preserves the saved noise/information comparison;
`residual-decomposition.json` preserves the motion/sensor/science attribution and input hashes;
`verification.json`
records the independent matching/provenance checks. The complete six-task evidence is in
`run/campaign.json`, the append-only shard journals and task-linked diagnostic files.

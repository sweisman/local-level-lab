# Correcting apparent tilt caused by aircraft acceleration

An IMU's accelerometer responds to both gravity and aircraft acceleration. Its apparent
vertical direction can change when the aircraft speeds up, slows down or changes course,
even without an equivalent IMU tilt. The current analysis can subtract that change as a
rotation. The preceding saved-data audit identified this as the main source of excess
variation in the six-case Chicago–Los Angeles replay.

A research prototype now estimates acceleration from the saved GPS observations and
removes its effect before recovering the vertical direction and aircraft rotation.
It uses the actual saved accelerometer magnitudes, recovered mount mappings and forward
reference. It does not use prescribed simulator motion to construct the correction.
Simulator motion is used separately, afterward, to measure its error.

The prototype filters GPS velocity and IMU force over the same time support. It recovers
orientation iteratively, differentiates orientation before averaging into minutes, and
refuses to cross GPS gaps, incomplete IMU coverage or unresolved mount turns. GPS fixes
must be frequent: the public position tracks alone cannot provide this correction.

## Results from the saved replay

All six existing analyses were assessed; no flight was generated and no model was refitted.
The nominal configuration was fixed at a 30-second filter, the recovered forward direction
and zero additional crab offset/rate. It was not selected using simulator truth.

| Diagnostic, using the same supported minutes | Result |
|---|---:|
| Original retained minutes | 99 |
| Minutes supported by the nominal correction | 85 |
| Minutes supported under every sensitivity state | 83 |
| Original residual on the nominal 85 minutes | 33.75–33.89°/hour |
| Residual after replacing motion correction, with model parameters held fixed | 11.12–11.20°/hour |
| Motion error against prescribed replay motion after correction | 10.05–10.12°/hour |
| Sensitivity states per analysis | 93 |
| Failed states after local support handling was corrected | 0 |

The improvement is substantial, but wind and orientation assumptions remain consequential.
Across the common 83 minutes, sensitivity states produce residuals of about9.6–37.3°/hour.
The grid varies 15/30/60-second filtering, crab offsets up to15°, crab drift up to3°/hour
and forward-direction offsets up to three reported standard errors. Twelve additional
controls perturb GPS-derived acceleration or measured force by three propagated marginal
standard errors. All states and unsupported samples are preserved; the most favorable state
is not promoted or selected as a decision rule.

GPS and IMU error propagation currently assumes independent observations. The grid is a
sensitivity study, not a confidence region. Correlated errors, instrument offsets and
scale errors, model-dependent acceleration terms and the full physical wind model still
need treatment. Motion bandwidth also changes with filtering. The saved science, bias and
crab coefficients remain fixed in these comparisons, so these results do not establish
refitted model separation, power or calibrated coverage.

Eleven focused checks pass, including independent fixed-mount acceleration, actual roll,
combined yaw/pitch/roll, filter uncertainty, timestamp/gap and bin-support fixtures.
Production analysis and all frozen campaign records are unchanged. The prototype cannot
make a scientific decision.

## Preserved evidence

| File | Purpose |
|---|---|
| `support-corrected/review.json` | Current assessment, fixed state definitions, per-state support/errors and source/input hashes. |
| `support-corrected/observed-input-0.npz` through `observed-input-4.npz` | Corrected motion/up arrays and support masks, grouped by identical source identities. |
| `support-corrected/verification.json` | Hash, task, state and dependency checks. |
| `review.json` and `observed-input-0.npz` through `observed-input-4.npz` | Initial diagnostic: six uncertainty states failed globally when individual samples crossed the acceleration bound. |
| `initial-acceleration-motion.py` | Exact source snapshot for that initial diagnostic. |

The support repair retains the same acceleration limit. Samples outside it now become
local exclusions; every minute touching their unsupported derivative support is excluded.
It does not expand the accepted acceleration range. The initial results remain preserved.

Implementation: `analysis/tests/acceleration_motion.py`; saved-data runner:
`analysis/tests/review_acceleration_motion.py`; fixtures:
`analysis/tests/test_acceleration_motion.py`. The current prototype is deliberately outside
the production analysis package and has a versioned policy with decision use disabled.

Next, couple acceleration-aware orientation to the wind/forward nuisance parameters in a
research prediction, propagate their joint uncertainty, and verify the remaining motion
error. Existing saved observations can support that development before a separately scoped
refit or new simulation campaign. Fresh calibration remains premature.

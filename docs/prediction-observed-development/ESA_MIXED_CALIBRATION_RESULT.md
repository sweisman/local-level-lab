# How combined calibration changes affect the ESA forecasts

All three model checks on recording 187 passed. The scalar integrator
reproduced each sealed nominal forecast to within one nanometre. It then
changed three calibration combinations individually and together, keeping
every step inside the original parameter bounds.

| Model | Later interaction RMS at step 0.01 | Later interaction RMS at step 0.10 | Earlier / later total RMS displacement at step 0.10 |
|---|---:|---:|---:|
| Globe with specified field | 0.128 mm | 12.8 mm | 0.064 m / 0.427 m |
| Globe with zero field | 0.082 mm | 8.19 mm | 77.5 m / 240 m |
| Disc with zero field | 0.080 mm | 7.97 mm | 80.1 m / 248 m |

Interaction is the difference between changing all three together and
adding their three separate effects. After including pair interactions,
the largest remaining three-way error over all later queries was under
0.002 mm. These figures isolate interactions between the tested changes.
The separate [single-direction check](ESA_TANGENT_REMAINDER_RESULT.md)
measures the departure from a first-order forecast along each direction.

The concentrations of parameters at their limits matter. Making all
changes feasible preserved the original directions for the specified-field
fit. In the two zero-field fits it removed outward components, breaking
some of the cancellations that had made the directions weak in training.
At step 0.10, the saved training Jacobian puts the three combined changes
at about 0.0018, 1.43 and 1.47 standardized RMS units, respectively.
A common step in parameter units therefore probes very different regions
of earlier fit quality. The next comparison should define the region by
earlier fit quality and the original bounds before testing forecast error.

This study made 45 value sweeps, zero new fits and zero reads of withheld
receiver positions or reserved flights. It compares calibration response
on one development flight and supplies no uncertainty coverage or model
decision.

[Fixed study plan](ESA_MIXED_CALIBRATION_PLAN.md)

Closed study ID `esa-mixed-calibration-v1-20261118`. Manifest SHA-256
`17c12dc3c4852668ca5ef86011648c51d72d1d362ab1bafefd52ce637101af2a`.
Each candidate's sealed `mixed-changes.json` contains the parameter steps,
the pair and three-way effects and the RMS and maximum errors.

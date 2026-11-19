# The earlier fit limits how far calibration can move

For each of the three saved ESA fits, the check scaled the combined
calibration direction by the increase in the original earlier loss.
The two allowances were 0.001 and 0.01 in total squared standardized
residual. They are sensitivity scales. The original parameter bounds
and 0.10 step cap still apply.

| Model | Step at 0.001 allowance | Later RMS shift | Step at 0.01 allowance | Later RMS shift |
|---|---:|---:|---:|---:|
| Globe with specified field | 0.0219 | 94.2 mm | 0.10, capped | 427 mm |
| Globe with zero field | 0.000000829 | 1.99 mm | 0.00000828 | 19.9 mm |
| Disc with zero field | 0.000000505 | 1.25 mm | 0.00000504 | 12.5 mm |

The allowances apply to the increase from each model's own training
fit. The starting losses were 5.15, 4,325 and 9,861 respectively.
The selected steps use the saved linear approximation to the earlier fit.
The later shifts come from propagating those steps in the nonlinear
integrator, without reading later receiver positions.

The guaranteed bound derived from the receiver's independent white
covariance was too loose for all six steps. At the smaller allowance,
upper limits on the actual earlier loss increase ranged from 49.6 to
554. The calculation cannot tell whether the steps exceed the allowances
under the archived full covariance. To answer that, rebuild and save the
full earlier whitening operation once per model and use it to score the
finite displacements directly. The aircraft error law still needs
independent support.

All three diagnostic tasks completed with nine value sweeps and no
optimizer starts. No withheld receiver reports or reserved flight
groups were opened.

[Fixed study plan](ESA_EARLIER_FIT_COST_PLAN.md) ·
[Original mixed-calibration study](ESA_MIXED_CALIBRATION_RESULT.md)

Closed study ID `esa-earlier-fit-cost-v1-20261118`. Manifest SHA-256
`3d76596ba7b4aee7389f613182b5556a4bd0abc600b9c79b8b644fe0b57112ea`.
Each sealed `earlier-cost.json` records both steps, the actual position
shifts and the full cost intervals.

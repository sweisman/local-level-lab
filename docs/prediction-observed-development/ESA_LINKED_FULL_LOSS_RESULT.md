# Removing fixed earlier residual energy barely changes the calibration bound

The revised calculation leaves the combined upper bound at **53.04 units**.
The zero-field globe–disc forecast gap is **25.41 units**. The two forecasts
remain unresolved over the full calibration range under this bound.

For each of eleven calibration boxes, the check found an earlier-residual
direction that the saved linear model could change very little. After
allowing for outward projection uncertainty and all coordinates in the box,
the direction accounted for just **0.024% to 0.067%** of the allowed squared
error. The remaining error budget was almost as wide as before.

| Model | Calibration boxes | Previous upper bound | Revised upper bound |
|---|---:|---:|---:|
| Zero-field globe | 5 | 20.63679538 | 20.63679538 |
| Zero-field disc | 6 | 32.40109866 | 32.40109865 |

Five individual bounds tightened. The combined bound fell by about
**7 × 10⁻⁹** units. None of the boxes could be excluded. All 22 numerical
proposals used their full 128-evaluation allowance. Both exact certificate
calculations checked every resulting score bound. The certificates preserved
the feasible calibration points already verified in the earlier work.

These results apply to the saved affine reconstruction and its calibration
representation. Most of the earlier error energy lies outside the direction
that this approach can set aside. A stronger bound would need to constrain how
the physical calibration moves the earlier trajectory. The full integration
remainder remains a separate requirement.

All eleven tasks completed in 45.33 seconds on three one-thread workers. Eleven
software checks passed. The run used 77 charged operations, zero new model
fits or integrations, and no later receiver positions or reserved flights.

[Frozen method](ESA_LINKED_FULL_LOSS_PLAN.md) ·
[Bounds by calibration box](esa-linked-full-loss-result.json) ·
[Verified run evidence](esa-linked-full-loss-evidence/README.md)

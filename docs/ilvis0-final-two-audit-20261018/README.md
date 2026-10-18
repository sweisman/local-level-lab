# Why two stretches remain unresolved

The saved checks distinguish problems with timing boundaries from unstable joint calibration corrections. This audit examines nine earlier diagnostic outcomes and fourteen branch reports; it performs no fits, integrations or numerical solves. The published tally remains **51 globe / 0 flat / 2 unresolved**.

| Stretch / case / model / start | Saved outcome | Fresh correction issue |
|---|---|---|
| `370cec66878c4c1cf84b4ceb / bias1_unsubtracted / sphere_rotating / primary` | two_sided_boundary_stability | None in the saved branch metrics |
| `370cec66878c4c1cf84b4ceb / bias1_unsubtracted / sphere_rotating / repeat` | two_sided_boundary_stability | None in the saved branch metrics |
| `370cec66878c4c1cf84b4ceb / bias1_profiled_removal / sphere_rotating / primary` | boundary_check_unresolved | right: fresh_stationarity, cost, position |
| `b4e44ddc0f130ecd45674c78 / bias1_unsubtracted / sphere_rotating / primary` | boundary_check_unresolved | right: fresh_stationarity, cost, position |
| `b4e44ddc0f130ecd45674c78 / bias1_unsubtracted / sphere_rotating / repeat` | two_sided_boundary_stability | None in the saved branch metrics |
| `b4e44ddc0f130ecd45674c78 / bias1_unsubtracted / sphere_still / primary` | side_geometry_unsupported | None in the saved branch metrics |
| `b4e44ddc0f130ecd45674c78 / bias1_profiled_removal / sphere_rotating / primary` | boundary_check_unresolved | None in the saved branch metrics |
| `b4e44ddc0f130ecd45674c78 / bias1_profiled_removal / sphere_rotating / repeat` | boundary_check_unresolved | right: fresh_stationarity, cost, position |
| `b4e44ddc0f130ecd45674c78 / bias1_profiled_removal / sphere_still / primary` | side_geometry_unsupported | None in the saved branch metrics |

## Nearby timing solutions

For `370cec66878c4c1cf84b4ceb`, the unsubtracted specified-field primary and repeat already pass. The profiled-removal primary passes the left check but fails the right fresh correction: its largest changes are in gravity, Y gyro gain and Z acceleration offset. The right correction changes the objective by about 0.049% and the reconstructed position by up to 20 mm RMS per axis, above the 1 mm numerical limit. Its endpoint side gradients pass; the new corrected point does not. The interrupted profiled-removal repeat has no completed diagnostic and remains a preserved failure.

A focused complete-cluster check from both original, fully saved fit endpoints can test whether a nearby supported boundary avoids this unstable correction. It must retain the full two-sided test, source-to-final movement limits and processing-case repeat comparison. It cannot reuse the interrupted identity or its allowance.

## Separated timing solutions and additional calibration failures

For `b4e44ddc0f130ecd45674c78`, the two zero-field-globe primaries stopped at the old geometry guard. They have not failed a measured-position stability test. The separately qualified representability check is relevant, but the saved primary/repeat time separation also calls for a bounded nonlinear timing profile. The specified-field failures reach an unchecked neighboring boundary on the right. Two also take a full-span gravity correction with metre-scale position changes; one has stable movement but still lacks the neighbor check. Thus checking a neighbor alone cannot justify accepting every endpoint.

The reports save aggregate stationarity values, not the fresh per-coordinate gradients. Large normalized correction components suggest where to inspect the numerical solve; they do not establish that gravity or a sensor calibration is physically wrong. No model preference is inferred from these failures.

[Current status](../CURRENT_STATUS.md) · [Next steps](../NEXT_STEPS.md) · [Finite audit plan](PLAN.md).

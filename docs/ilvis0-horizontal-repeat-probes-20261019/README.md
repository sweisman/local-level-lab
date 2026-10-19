# Fixed-point diagnosis of horizontal repeat failures

Completed **28 native tangent evaluations**, with zero optimizer starts. All eight saved centers reproduced before their diagnostic points were evaluated. No fit or repeat labels changed.

| Endpoint | Point | Scored cost | Fresh stationarity | Horizontal change RMS (m) | Height change RMS (m) |
|---|---|---:|---:|---:|---:|
| b365bdf39150ee6afc303ac1::bias1_unsubtracted::sphere_rotating::primary | center | 5.2195721 | 1.34953e-07 | 0 | 0 |
| b365bdf39150ee6afc303ac1::bias1_unsubtracted::sphere_rotating::primary | affine | 5.2195721 | 3.51772e-09 | 1.00777e-07 | 0.00969325 |
| b365bdf39150ee6afc303ac1::bias1_unsubtracted::sphere_rotating::repeat | center | 5.2195721 | 1.79921e-08 | 0 | 0 |
| b365bdf39150ee6afc303ac1::bias1_unsubtracted::sphere_rotating::repeat | affine | 5.2195721 | 3.13461e-10 | 1.44713e-08 | 0.00125891 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::primary | center | 5.5641762 | 3.9576e-08 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::primary | coordinate_swap | 18.735606 | 0.837887 | 4.43145 | 5.16361 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::primary | full_midpoint | 5.5695007 | 0.00195122 | 0.00394815 | 2.47641 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::primary | affine | 5.5641762 | 4.02178e-09 | 1.89563e-07 | 0.0001977 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::repeat | center | 5.5730736 | 2.28497e-07 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::repeat | coordinate_swap | 18.726709 | 0.838108 | 4.43145 | 5.16365 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::repeat | full_midpoint | 5.5695007 | 0.00195122 | 0.00385055 | 2.47392 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::sphere_still::repeat | affine | 5.5730736 | 1.4157e-08 | 1.77856e-06 | 0.000387761 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::primary | center | 3645.6083 | 2.08143e-08 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::primary | coordinate_swap | 3645.6083 | 2.08143e-08 | 0 | 668.598 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::primary | full_midpoint | 3645.6083 | 1.97565e-06 | 0.000657576 | 326.599 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::primary | affine | 3645.6083 | 6.86255e-07 | 3.25932e-05 | 3.02618e-07 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::repeat | center | 3645.6083 | 3.97684e-06 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::repeat | coordinate_swap | 3645.6083 | 3.97684e-06 | 0 | 668.598 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::repeat | full_midpoint | 3645.6083 | 1.97565e-06 | 0.000657375 | 326.599 |
| 7df21c836bec5751f83c0cce::bias1_unsubtracted::flat_still::repeat | affine | 3645.6084 | 9.79765e-06 | 0.000702746 | 7.86299e-06 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::primary | center | 5.5641762 | 3.9562e-08 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::primary | coordinate_swap | 18.735605 | 0.837887 | 4.43145 | 5.16361 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::primary | full_midpoint | 5.5695007 | 0.00195122 | 0.00394815 | 2.47641 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::primary | affine | 5.5641762 | 3.99219e-09 | 1.89428e-07 | 0.000197602 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::repeat | center | 5.5730736 | 2.28493e-07 | 0 | 0 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::repeat | coordinate_swap | 18.726709 | 0.838108 | 4.43145 | 5.16365 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::repeat | full_midpoint | 5.5695007 | 0.00195122 | 0.00385055 | 2.47392 |
| 7df21c836bec5751f83c0cce::bias1_profiled_removal::sphere_still::repeat | affine | 5.5730736 | 1.41689e-08 | 1.77858e-06 | 0.000387849 |

The probes test competing timing/calibration directions at fixed points. An improved score is not a converged fit or a passed repeat; the two-recording sensitivity study and original 53-stretch findings retain their published labels.

[Frozen scope](PLAN.md) · [Saved-fit diagnosis](../ilvis0-horizontal-repeat-audit-20261019/README.md).

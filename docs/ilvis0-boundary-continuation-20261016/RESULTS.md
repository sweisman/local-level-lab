# Timing-boundary continuation results

Completed 12 identities with 233 native evaluations. These are local timing and stopping diagnostics, not new scientific model comparisons. Original labels remain unchanged.

| Stretch | Endpoint | Kind | Diagnostic passed | Native calls | Outcome |
|---|---|---|---|---:|---|
| `50f24131843071ae9312c082` | bias1_unsubtracted::sphere_still::primary | time_only | True | 24 | two_sided_boundary_stability |
| `50f24131843071ae9312c082` | bias1_unsubtracted::sphere_still::repeat | time_only | False | 0 | KeyError: (np.float64(-0.3077346241962242), np.float64(0.06262586226943415), np.float64(0.2915022673179837), np.float64(-0.029342916024680768), np.float64(0.035426462566572135), np.float64(-0.007887896448919188), np.float64(-0.11587243591879624), np.float64(0.01697552637152188), np.float64(0.11849653734088829), np.float64(-1.0), np.float64(0.43153454245099737), np.float64(-1.0), np.float64(-1.0), np.float64(-1.0), np.float64(1.0), np.float64(1.0), np.float64(1.0), np.float64(-1.0), np.float64(1.0), np.float64(-1.0), np.float64(0.19616715278150967), np.float64(1.0), np.float64(1.0), np.float64(-1.0), np.float64(-1.0), np.float64(-0.43810412716244257)) |
| `b4e44ddc0f130ecd45674c78` | bias1_unsubtracted::sphere_rotating::primary | time_only | False | 22 | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78` | bias1_unsubtracted::sphere_rotating::repeat | time_only | True | 24 | two_sided_boundary_stability |
| `b4e44ddc0f130ecd45674c78` | bias1_unsubtracted::sphere_still::primary | time_only | False | 13 | side_geometry_unsupported |
| `b4e44ddc0f130ecd45674c78` | bias1_profiled_removal::sphere_rotating::primary | time_only | False | 23 | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78` | bias1_profiled_removal::sphere_rotating::repeat | time_only | False | 22 | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78` | bias1_profiled_removal::sphere_still::primary | time_only | False | 13 | side_geometry_unsupported |
| `bb8061a43b4f14b6262ceda1` | bias1_unsubtracted::sphere_still::primary | time_only | False | 23 | boundary_check_unresolved |
| `bb8061a43b4f14b6262ceda1` | bias1_unsubtracted::sphere_still::repeat | time_only | False | 23 | boundary_check_unresolved |
| `fd7b81e48a4122b149c4925b` | bias1_profiled_removal::sphere_still::primary | time_only | True | 23 | two_sided_boundary_stability |
| `fd7b81e48a4122b149c4925b` | bias1_profiled_removal::sphere_still::repeat | time_only | True | 23 | two_sided_boundary_stability |

The three already-passing smooth repeats remain untouched. Any recovered numerical comparison still requires all model/case companions and scheduled repeat checks.

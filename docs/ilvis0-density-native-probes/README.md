# Do the large linear changes survive the full model?

12/12 numerical diagnostics pass; 0/12 proposed calibrations satisfy nonlinear training constraints.

| Processing | Target direction | Outcome | Largest training change | Later N / E / height change |
|---|---|---|---:|---:|
| Zero removal | N − | Rejected by nonlinear training | 131.049 m | 139.682 / -151.918 / -48.981 m |
| Zero removal | N + | Rejected by nonlinear training | 113.714 m | 387.477 / -62.506 / -64.487 m |
| Zero removal | E − | Rejected by nonlinear training | 280.358 m | -674.843 / -747.770 / 183.216 m |
| Zero removal | E + | Rejected by nonlinear training | 377.256 m | -775.961 / -590.986 / 171.998 m |
| Zero removal | height − | Rejected by nonlinear training | 370.537 m | -833.989 / -46.979 / 167.703 m |
| Zero removal | height + | Rejected by nonlinear training | 325.274 m | -709.794 / -115.057 / 176.975 m |
| Profiled removal | N − | Rejected by nonlinear training | 1,448.235 m | 1,551.880 / -3,290.637 / 557.264 m |
| Profiled removal | N + | Rejected by nonlinear training | 1,119.252 m | 1,238.552 / -2,335.837 / 392.960 m |
| Profiled removal | E − | Rejected by nonlinear training | 1,737.923 m | -795.899 / -3,990.738 / 760.323 m |
| Profiled removal | E + | Rejected by nonlinear training | 1,808.588 m | -1,769.949 / -3,749.007 / 794.921 m |
| Profiled removal | height − | Rejected by nonlinear training | 1,245.998 m | -2,747.928 / -1,968.151 / 551.988 m |
| Profiled removal | height + | Rejected by nonlinear training | 912.192 m | -2,038.198 / -1,855.730 / 403.599 m |

Every proposal was selected from saved Jacobians, checked exactly, contracted by the fixed 0.99 factor and saved before the nonlinear outcome. The training check uses only the 292 earlier positions and the unchanged ±1 m allowance. The later displacement cannot decide that label.

This is a generated-data diagnostic around the saved zero-expansion reference, not an aircraft fit or the separate long-record run’s perturbed training data. Rejected sampled points do not prove unique prediction or permit removal of unexamined parameter regions. No uncertainty coverage, observation-error law or scientific significance is established.

[Frozen scope](PLAN.md) · [Training-density results](../ilvis0-training-density/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

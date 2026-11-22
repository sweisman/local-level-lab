# Recorded-data optimizer preflight

The separate one-task SciPy TRF preflight completed on a preselected NASA
development recording. It exercised the frozen input adapter, native-call
charging, continuous forecast output and result sealing before the 24-fit
method comparison began.

The task was capped at 30 optimization calls and used all 30. It **did not
meet the full numerical convergence check**. Its pass means the worker and
evidence path completed correctly; this preflight was never intended to
qualify a scientific fit. The full study keeps its separately frozen
200-evaluation limit and must report convergence for every fit.

The sealed result records one technical completion, zero worker errors,
46,082,763 charged packet visits and an `abstain` scientific decision.
The source/input manifest SHA-256 is
`32b1c8dfc0e916560012b4eb7de011c9af6591a30fecfb5f4c1f36f188ebfcb8`;
the summary SHA-256 is
`bb81362f63da835edbc7210ce563f32d6e32b711ca3406a6dd4f3ef0eac74a61`.
The [versioned plan](OBSERVED_METHOD_PILOT_V2_PLAN.md) fixes the subsequent
recording selection and task grid. The earlier 80-fit development labels and
all protected confirmation recordings remain unchanged.

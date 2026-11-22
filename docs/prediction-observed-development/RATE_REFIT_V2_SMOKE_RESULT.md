# ESA rate refit: generated software check

The corrected six-task generated check is complete: **6/6 technical tasks
passed**, with no task errors. All six reproduce their original saved
training fit and forecast within the frozen numerical tolerances. Each also
reproduces the original generated fit's **nonconverged** status at the short
eight-evaluation smoke limit. This is a software check, not a successful
scientific fit or an aircraft result.

This generated control has no separate raw rate stream, so its three method
labels intentionally use the same increments. Separate source-bound tests
check the three conversions against the saved real rate samples; the smoke
check verifies the fit and forecast pipeline, not which conversion the iMAR
instrument actually used.

The first smoke study remains a separate, sealed terminal result. It failed
because its gate demanded numerical convergence from those deliberately
short controls. The corrected study used one numerical thread, charged
60,000 native calls and six million packet/query visits across six tasks,
and opened no protected flight group.

The next gate is a source-bound passing test suite, followed by six
training-only refits on the already selected ESA development recording. Those
observed fits must converge under the unchanged rule; later receiver
measurements remain withheld until the forecasts are sealed. The present
scientific decision is **abstain**.

[Frozen plan](RATE_REFIT_V2_PLAN.md).

Completed study manifest:
`6137e8c1ac18e863c44d01aefbc3b452accaf9663e8dc8d02a12939039c4c843`.
Summary:
`dfca139a8883b82f0f9af451ce94ab7a515b45bd630818eb2aae7b0a15b83091`.

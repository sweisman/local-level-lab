# The complete generated fits expose a prediction failure

The [frozen pilot](FULL_FIT_INNOVATION_NULL_PLAN.md) closed both 600-report
generated tasks in about 19 minutes. Both 26-parameter fits converged in
seven evaluations and retained full tangent rank. The study's **overall
gate failed**: neither generated trajectory passed its predeclared physical
accuracy screen. The sealed state is `terminal`, and its failures remain
counted.

| Generated truth and fitted law | Height error after whitening, RMS | Correlation one report apart | Correlation 20 reports apart | Training horizontal RMS versus known truth | Later horizontal RMS versus known truth |
|---|---:|---:|---:|---:|---:|
| Increment | 0.999 | +0.023 | −0.073 | 55.3 m | 219.2 m |
| Point | 0.972 | +0.012 | −0.029 | 33.3 m | 156.1 m |

The opened ESA recording instead has fitted height correlations of **0.825**
and **0.538** at those lags under either law. This pilot shows that the
complete nonlinear fit, with the two declared generated error processes, does
not itself reproduce that persistent ESA height pattern. Two generated
histories cannot calibrate how unusual the ESA pattern is, and their aircraft
trajectory and receiver errors differ from the recorded flight.

The more consequential result is that **good fitted training innovations did
not guarantee a good physical trajectory**. The frozen screen allowed at
most 10 m horizontal RMS in each section; both generated cases exceeded it
even in training, and their later errors grew substantially. The whitening
law describes residuals around a fitted path, while uncertainty in that
path and its calibration can still be large. No success is inferred from the
two numerical convergences.

The next error-law design must cover full-trajectory and calibration error
over the chosen horizon, then pass new, independently generated complete-fit
controls before any aircraft uncertainty claim. The seven ESA confirmation
groups remain unopened; the scientific decision is **abstain**.

A [saved-path audit](GENERATED_PATH_ERROR_AUDIT_RESULT.md) shows that the
generated receiver positions are within 0.4 m horizontal RMS of truth during
training, while the two fitted paths are 33–55 m away and drift farther over
time. This separates receiver noise from the much larger fitted-path error
in these two examples without changing the pilot outcome.

[Saved fit audit](full-fit-innovation-null-result.json) ·
[Local fit projection](LOCAL_PROJECTION_NULL_RESULT.md) ·
[Saved ESA error pattern](INNOVATION_MORPHOLOGY_RESULT.md)

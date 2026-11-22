# Next numerical gate for retrospective forecasts

The [twenty-group saved stopping audit](REMAINING_GROUPS_STOPPING_AUDIT.md)
found 49 fits that passed their initial stationarity check but failed the
frozen fresh cost-change limit of `1e-8`. Five of those also failed fresh
stationarity. None failed the specified training-position change limits or
used its full evaluation allowance. The median failed cost change was
`4.48e-8`; the largest was `2.47e-5`. All 50 original nonpassing labels stay
unchanged.

The next solver qualification must answer whether a numerically different
solution would make a materially different **withheld-position forecast**.
Similar training costs or positions alone cannot answer that, because weak
calibration directions may grow during an uncorrected forecast.

1. Use independently generated known-answer IMU and receiver histories, with
   all three physical candidates, both clock interpretations, interior and
   boundary calibrations, and deliberately weak directions. Keep the true
   trajectory separate from the estimator.
2. Compare at least two bounded numerical methods on identical inputs and
   the same permitted physical parameter box. Score objective agreement,
   fresh stationarity, training-position stability and later **forecast-path**
   agreement before looking at generated truth.
3. Choose any revised stopping rule and a useful forecast-stability tolerance
   from the generated development controls. Freeze its source, thresholds,
   environment and finite charges before independent generated confirmation.
   Count every failed fit against the confirmation gate.
4. Only after that, run a separately frozen, reboot-resumable observed
   development comparison. Select its recording groups without using the new
   forecast outcomes. Preserve every original fit and the 80-task study
   unchanged. Reserved ESA confirmation groups remain closed.

The first [saved-path diagnostic](REMAINING_GROUPS_CORRECTION_DIAGNOSTIC.md)
reconstructed all 49 bounded corrections from retained residuals and
Jacobians, verifying their predicted changes against the recorded probes.
The corrected parameter vectors were not retained in the original study;
they are now separate diagnostic artifacts. A [separately charged three-case
forecast check](CORRECTION_FORECAST_RESULT.md) found path changes up to
16.3 mm in its preselected numerical range without reading later receiver
positions. It cannot retroactively pass a failed fit, establish forecast
accuracy, or replace the independent generated controls above.

The first [generated forecast control](GENERATED_SOLVER_FORECAST_RESULT.md)
has now passed 24/24 fits and all six four-fit comparisons across three
physical models and two clock constructions. It uses independently generated
12-second paths and six free calibration parameters. The next qualification
must expose all 26 archive calibration directions, weakly constrained and
noisy histories, and a longer withheld period before a changed stopping rule
can be frozen. The observed 50 nonpassing labels remain unchanged.
The [four-fit pilot](FULL_CALIBRATION_SOLVER_RESULT.md) closed all four
full-calibration noisy generated fits and found later-path agreement between
the two bounded solvers and two starts. The [multimodel control](MULTIMODEL_SOLVER_RESULT.md)
then passed all 24 generated fits and all six four-fit gates across three
models and two calibration settings. Those six cases share a declared noise
seed. The [nominal 200 Hz control](NOMINAL_200HZ_SOLVER_RESULT.md) then passed
24/24 fits and 6/6 agreement gates under six distinct noise seeds. Its exact
sample grid does not test irregular header timestamps. The [longer generated
confirmation](LONG_HORIZON_SOLVER_RESULT.md) then passed all 24 fits and six
preregistered solver/start forecast-agreement gates on 120-second histories.
The [saved two-start aircraft audit](REMAINING_PAIR_AGREEMENT.md) found all
40 original forecast pairs within 0.1 m, with a maximum difference of
6.03 mm. A separately frozen observed development method may now test
forecast stability as its own numerical property. It must retain the
50 original nonpassing fit labels and cannot call a stable forecast an
optimized fit, a calibrated prediction or a scientific detection.
The [solver-independence correction](SOLVER_INDEPENDENCE_ERRATUM.md) narrows
the generated qualification: the two named providers share the same
trust-region optimizer. A genuinely different bounded method must pass
before using optimizer agreement as evidence of numerical stability on
aircraft data.
The [short independent-method control](INDEPENDENT_SOLVER_RESULT.md) has now
passed all 24 fits and six generated agreement gates using SciPy TRF versus
the trust-region optimizer. This repairs the method-diversity gap for those
short generated inputs. The [120-second independent-method control](LONG_INDEPENDENT_SOLVER_RESULT.md)
also passed all 24 fits and six generated agreement gates after a finite,
hash-verified recovery of four tasks interrupted by a host reset. These
controls led to a separate observed real-worker preflight and a finite
development comparison on three preselected recordings. Neither generated
control establishes aircraft prediction accuracy. The
[recorded-input preflight](OBSERVED_METHOD_V2_PREFLIGHT.md) passed its worker
wiring check but did not converge under its 30-call smoke-test cap. The
versioned [24-fit observed comparison](OBSERVED_METHOD_PILOT_V2_RESULT.md)
has now closed within its finite limits. All fits completed technically, but
only 7/24 met numerical stopping checks and 4/6 matched sets met the
development path-agreement scale. The
[saved-result diagnosis](OBSERVED_METHOD_V2_DIAGNOSIS.md) has classified all
17 nonstopping fits and both disagreeing cuts. Ten fits fail only the relative
cost-change check; the two disagreeing cuts also have the largest fitted
time-offset spreads. That motivated a fixed-endpoint timing and
cost-repeatability check on those cuts and matched stable controls.
The [fixed-endpoint check](OBSERVED_FIXED_ENDPOINT_RESULT.md) has now closed:
8/8 exact same-point replays, 80/80 calls charged, and timing derivatives
close to finite differences even where packet intervals change. The 2010
maximum path pair differs by only 0.004 ms in fitted time offset; the 2015
pair differs by 11.237 ms. Next: analyze joint calibration valleys and
later-path sensitivity on these saved development solutions before proposing
another optimizer. Preserve original bounds, measurements and failed labels.
No aircraft fit has been reclassified or promoted to a scientific detection.
The [fixed calibration-swap check](OBSERVED_CALIBRATION_SWAP_RESULT.md) then
completed all 24 declared vectors without refitting. Whole-vector swaps
reproduce the original forecasts exactly, while isolated calibration-group
swaps substantially worsen the training cost and can move later forecasts
by hundreds of metres. This shows strong coupling between fitted groups;
those isolated hybrids are not acceptable alternative fits. The next fixed
check should trace the cost and forecast along the complete parameter-vector
connection between each pair, before a revised numerical method is proposed.
That [six-point complete-vector check](OBSERVED_PAIR_PATH_RESULT.md) has now
closed without refitting. The 2010 pair has a modest midpoint cost rise;
the 2015 pair stays near the endpoint costs. Both pairs retain later-path
differences. A straight line cannot exclude a curved low-cost connection.
The next method qualification must test whether independent bounded
optimizers and starts recover stable forecasts under the same recorded
calibration box and genuinely independent generated truth; the original
aircraft stopping failures remain failures.

The [continuation runbook](INDEPENDENT_METHOD_RUNBOOK.md) gives the frozen
status and resume commands for the long control and its gated observed pilot.

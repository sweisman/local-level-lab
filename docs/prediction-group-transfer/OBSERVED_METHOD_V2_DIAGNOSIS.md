# Why the recorded-data method did not qualify

The [24-fit pilot](OBSERVED_METHOD_PILOT_V2_RESULT.md) used three previously
selected aircraft recordings. Every fit finished and saved a prediction for
receiver positions that had been held out of calibration. That establishes
that the software ran; it does not establish that the numerical answer was
stable or that its prediction was physically adequate.

Only 7 of 24 fits passed the frozen numerical stopping checks. Of the other
17, two failed the stationarity check before a fresh probe could be made.
Fifteen completed a fresh probe but failed its combined check. All fifteen
exceeded the relative cost-change limit of 10⁻⁸. Five also exceeded the
stationarity limit of 10⁻⁴, and three also exceeded the position-change
limit (1 mm RMS or 1 cm maximum on any axis). Ten failed **only** the
cost-change part of that combined check. A [saved-only audit](observed-method-v2-diagnosis.json)
reproduces these overlapping counts from the sealed fits, records their hashes
and makes no new model evaluations. Reproduce it with
`~/venv/bin/python -m lll.ilvis0_observed_method_diagnosis`. A failed stopping
check is preserved even when its forecast is close to another forecast.

Two of the six matched recording/cut sets exceeded the 0.1 m development
path-agreement scale: the inner cut of the 2010 northern recording differed
by up to 0.752 m, and the inner cut of the 2015 southern recording by up to
0.320 m. All six matched training-cost ranges were under 0.01. The small cost
ranges therefore do not guarantee matching later paths. The other four cuts
met the path scale, including cuts with nonstopping fits.
The saved path-pair identities show that the 2010 maximum is between the two
optimizers at the same start; the 2015 maximum is between two starts of SciPy
TRF. Both kinds of numerical variation matter.

The two differing cuts also have the widest spreads in fitted receiver/IMU
time offset: 6.0 ms and 11.2 ms. The four other cuts range from effectively
zero to 0.056 ms. The [audit records all six pairs](observed-method-v2-diagnosis.json).
This association points to timing as a useful next diagnostic; it does not
show that timing alone caused the forecast differences, because other fitted
parameters changed too.
The subsequent [fixed-endpoint timing check](OBSERVED_FIXED_ENDPOINT_RESULT.md)
replayed all eight selected solutions exactly. It found only a 0.004 ms
time-offset difference in the 2010 maximum path pair, versus 11.237 ms in
the 2015 pair. Timing alone therefore cannot be presumed to explain both.
The later [calibration-swap check](OBSERVED_CALIBRATION_SWAP_RESULT.md) found
that swapping a single parameter group sharply worsens training fit while
the complete paired solutions retain near-equal costs. Their calibration
changes compensate one another.

The seven stopping fits have later horizontal RMS errors from 0.45 to 9.76 m
and later height RMS errors from 0.07 to 5.05 m. All seven put Z-axis gyro
bias, Z-axis gyro gain and the gravity correction at their allowed bounds.
Those bounds are study assumptions, not measured instrument limits. Passing a
numerical stopping check therefore does not by itself establish an adequate
physical calibration or an accurate forecast.

The [saved accuracy audit](ACCURACY_MARGIN_RESULT.md) applies the unchanged
position-error screen from the transfer study to all 24 forecasts. All
24 meet those limits. The 17 nonstopping fits retain their failed numerical
labels, and the two cuts outside the forecast-agreement scale remain open.

The current gates must not be loosened simply to raise the pass count. Next,
use the saved costs, fresh probes, bound activity and forecast errors to
separate two questions: whether the cost-change tolerance is tighter than
the numerical precision that the recorded problem supports, and whether the
two differing forecasts reflect materially distinct feasible solutions,
including their fitted timing offsets.
Any changed stopping rule needs an independent generated control and a new
finite recorded-data study. The original 80 aircraft fits and this pilot keep
their saved labels.

This is a method diagnosis for one specified-field globe candidate. It is
not a globe-versus-flat result, a background-field estimate or a calibrated
scientific detection.

# Changing the training GPS export does not change this flight's ranking

The [finite six-fit study](ESA_ALTERNATE_TRAINING_REFIT_PLAN.md) changed only
the first 400 receiver positions used for fitting on the opened ESA
development flight. It used `mosaic03` or `pwrpak7` positions in place of
`air1`, while retaining the same IMU data, original `air1` covariance and
velocity, model method, numerical limits, start, and 120 later `air1`
positions for scoring. The [source audit](esa-alternate-training-source-audit.json)
verifies that every other training-row field is identical. No reserved
flight group was opened.

**All 6/6 fits passed their numerical checks**, with no technical errors.
The frozen four-worker study closed in 19.6 minutes; its 4.2 million
native-call ceiling was charged before execution. The
[machine result](esa-alternate-training-refit-result.json) binds the study,
parent and original-matrix receipts. The table gives total RMS error on the
same 120 later positions, in metres:

| Training positions | Globe, specified field | Globe, zero field | Flat disc, zero field |
|---|---:|---:|---:|
| Original `air1` | 5.227 | 2,590.069 | 3,998.249 |
| `mosaic03` | 4.744 | 2,587.193 | 3,998.911 |
| `pwrpak7` | 5.231 | 2,589.247 | 3,999.847 |

The specified-field globe has the lowest error and passes the existing
descriptive physical screen with either alternate training input. Relative
to the original forecasts, the new later paths move by 0.58–2.96 m RMS,
depending on model and export. Thus the centimetre-scale choice among
these three PPP training positions does **not** change the numerical
ordering in this preselected setting on this one flight.

This is a development sensitivity check, not independent confirmation. It
uses only the original primary start and one complete processing/noise
setting; the other settings were not silently relabeled. The later horizon
was selected after earlier work on this flight. All PPP exports share an
antenna and geodetic coordinate construction, so this test cannot detect
error common to them or remove coordinate assumptions. The aircraft
prediction-error law and full two-stage false-choice rate remain
uncalibrated. No Earth-model or causal-field detection is claimed.

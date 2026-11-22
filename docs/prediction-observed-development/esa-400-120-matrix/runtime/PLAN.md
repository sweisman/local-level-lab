# Matched Earth-model forecasts on the opened ESA flight

## Question

On the already opened ESA development recording, does a model fitted to the
first 400 receiver reports predict the next 120 reports better than the other
two models? This is an exploratory, matched, withheld-position comparison.
The 120-report horizon was selected after earlier outcomes on this same
recording were known. It is not independent validation or a calibrated
Earth-model decision.

## Exact cases and inputs

Use the hash-verified 400/120 cut from the completed earlier-origin study:
155,868 inertial intervals, receiver reports 0–399 for calibration, and only
the *times* of reports 400–519 during fitting. The later receiver positions
remain in a separate parent artifact until every fit and forecast has sealed.
No original file or reserved ESA flight group may be opened.

Freeze **24 identities**: three physical candidates (`sphere_rotating`,
`sphere_still`, `flat_still`) × two upstream-removal cases (zero and a common
fraction profiled within the existing bounds) × two previously declared IMU
error conventions (`increment`, `point`) × two fixed starts (0 and 1).
Use the same header-elapsed clock, height-dependent gravity, calibration
bounds, latency bound, 200-evaluation stopping rule and existing numerical
implementation as the completed 400/120 specified-field fit. Do not choose a
case, start or error convention after seeing later positions.

Each task may charge at most 700,000 native calls and 45,000,000,000 packet
visits, including the forecast. The full ceiling is 16,800,000 calls and
1,080,000,000,000 visits. Use four one-thread workers and an eight-hour
cooperative original wall limit. Prove and freeze finite task-level reboot
recovery before launch. Seal every pass, numerical failure, technical error
and interruption; completed outcomes never restart.

## Scoring and stopping rules

After all tasks close, select each model/processing/error-convention primary
by the lowest *converged training* cost, with start order breaking an exact
tie. Do not substitute a later-better start. Score complete forecasts in the
same receiver-coordinate chart and report north/east/height errors, horizontal
and vertical RMS, maxima, active bounds and numerical stopping status.
Apply the existing physical screen separately to training and prediction:
horizontal RMS ≤10 m, height RMS ≤30 m, maximum horizontal error ≤50 m and
maximum absolute height error ≤150 m.

A matched setting is complete only if all three training-selected primaries
converge and supply all 120 predicted positions. Compare the better globe
candidate with the tested disc first. Compare specified versus zero background
field only when the complete shape comparison favors globe. A relative
preference from an inaccurate preferred model is labeled **preferred but
inadequate**. Missing or failed fits produce **unresolved**, never support
for another model. No confidence or significance follows from these errors.

Require source/environment/input-bound software tests, a no-future-position
preflight, exact task and charge checks, and saved-result verification. The
existing 53-stretch NASA result and the seven reserved ESA flight groups stay
unchanged. A real-aircraft prediction-error law and calibrated two-stage
decision procedure remain separate prerequisites for a scientific detection.

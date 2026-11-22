# Complete-fit generated innovation pilot

## Question

When an aircraft follows an independently generated known trajectory and its
IMU and receiver errors obey one of the two declared laws, does the **complete
26-parameter nonlinear fit** itself leave persistent height innovations like
those in the opened ESA development recording?

This is a method pilot, not a calibrated aircraft error-law decision. It
follows the [saved generated reference](../prediction-simultaneous-law-family-v3/FITTED_INNOVATIONS_RESULT.md)
and the [local tangent control](LOCAL_PROJECTION_NULL_RESULT.md).

## Frozen design

- Two full generated tasks: one truth/fitted increment law and one truth/fitted
  point law. Both use the same specified-field globe, a 300 Hz IMU grid,
  900 seconds and 900 one-second receiver queries. The shared protocol places
  the first **600** receiver reports in training and 300 later reports outside
  the fit. Each task has one fixed start and one noise seed.
- Preserve the independently generated aircraft truth, recorded noisy
  increments, noisy receiver observations, original calibration bounds,
  26 nuisance directions and the existing convergence rule. Record every
  numerical failure. Analyze only the saved 600-report fitted innovations;
  do not tune or select a law from later outcomes.
- Run a nine-query, ten-second frozen-worker preflight first. Require source
  and recovery qualification, finite prepaid native and construction charges,
  no duplicate task starts, and completion verification before the full run.
  The short preflight checks artifact production, not numerical convergence.
  The full study has two workers of one numerical thread each, at most 200
  evaluations per fit and a six-hour cooperative wall cap. The preflight has
  one worker, eight evaluations and a ten-minute cap.
- Report lag-1, lag-5 and lag-20 height correlations, RMS and rank for each
  passing fit. Compare descriptively with the ESA training diagnostic. Two
  generated histories cannot establish a tail frequency or error-law
  adequacy. A subsequent separately frozen cohort and motion/error
  adversaries are required for calibration.

No original aircraft file, scored receiver result or reserved ESA group may
be read by the generated worker. No Earth-model decision follows. The
scientific decision remains **abstain**.

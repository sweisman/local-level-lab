# Resolving the remaining horizontal-only comparison

The original 53-stretch full-position analysis is complete. This work concerns
the separate two-recording sensitivity study: IMU8 is complete, while three
IMU21 repeat pairs disagree. It does not reopen completed allowances or expand
the recording cohort.

## Recovery method to qualify

1. Use the completed path and finite-difference evidence to distinguish a faulty
   derivative from separated local stationary solutions. Close the diagnostic
   allowance before any solver qualification. A small vector-derivative error
   is not sufficient to certify a nearly cancelled objective gradient.
2. Qualify a deterministic multi-start timing search on inexpensive known-answer
   nonlinear controls with timing/calibration coupling and multiple stationary
   points. Include active bounds and prediction-equivalent nuisance directions.
   Give both repeat searches the same predeclared start rule, independent of
   model ranking. Verify recovery of the known best cost and predictions, not
   merely successful stopping. Freeze start and evaluation limits before running.
3. Only after qualification, prepare a separate finite observed comparison.
   Preserve the original data, clock, physical bounds, covariance and score.
   Save every attempted start and failure. Compare the best fully checked
   solutions under a fixed selection rule and retain the existing repeat-cost,
   1 mm axis-RMS and 1 cm epoch-maximum requirements. A midpoint or a copied
   primary does not constitute an independent repeat.
4. Preserve the horizontal sensitivity outcome separately, even if it resolves.
   Report the unscored height paths and the flat model's invisible gravity
   direction. Gyro/acceleration contribution controls and unused-observation
   prediction remain necessary; horizontal scoring alone isolates neither IMU
   channel and does not establish adequate full-flight trajectories.

This plan defines the next qualification target. It contains no new observed
optimizer allowance and does not authorize reuse of a completed study's budget.

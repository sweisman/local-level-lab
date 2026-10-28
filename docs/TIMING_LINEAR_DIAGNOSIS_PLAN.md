# Check the saved bounded linear calculation

## Question

Can the current bounded linear calculation return a worse objective than a
feasible zero step while reporting success? The closed local-timing calibration
contains two such verification records. This review must distinguish saved
evidence from a reconstruction using a different linearization.

## Fixed selection and limits

Use the two failed starts for seed 281474977210667, increment input,
specified-field globe, no upstream-removal parameter. Include both prescribed
starts of the closest earlier completed seed with the same configuration and
two numerical passes. Select that control using training/completion metadata,
without later prediction errors. Bind the parent manifest, summary and fit hashes.

Use only each saved final residual, full 26-column Jacobian, fitted point and
the declared timing cell containing that exact point. Do not shift the anchor
or reconstruct unsaved residuals/Jacobians. This is a baseline-linearization
check, not an exact replay of the earlier verification at a different anchor.
Report the original saved verification metrics separately.

Freeze four records, at most four bounded linear solves, one numerical thread
and a 600-second cooperative ceiling. Charge before solving. No native calls,
nonlinear fits, new noise draws, aircraft observations or protected data.
Earlier unused allowances remain closed. Keep all columns and original bounds.

## Evidence and next gate

Recompute proposal residuals and costs with independent scalar arithmetic.
Report feasibility, the zero-step benchmark, cost change and the solver's
success flag separately. A completed diagnosis does not qualify a solver or
change any historical fit label. Preserve failures and missing outcomes.

After source-bound software checks, use the shared study lifecycle, verify the
closed results and publish a short report and CSV. Any proposed solver change
then needs independent known-answer tests before a separately frozen trial.
Calibration and validation cannot restart from this review.

[Closed calibration](prediction-calibration-timing/INTERPRETATION.md) ·
[Current roadmap](ANALYSIS_ROADMAP.md).

# Measurement-contribution development scope

## Purpose and preserved baseline

Explain the source of globe/disc separation after numerical recovery of all 53
preselected stretches. Preserve their complete comparisons, original observations,
interval selection, prior failures and publication gate. Do not infer independent
curvature evidence from the coordinate datum alone or use fused navigation as a
replacement for absent inertial observations.

## Implemented software control

`lll.ilvis0_observation_projection.ReceiverProjection` takes the original joint
receiver covariance and a fixed list of retained coordinates. If the full
whitening is L, selection is S and the retained covariance factor is Ls, the
projected objective is Ls⁻¹ S L r, where r is the original whitened residual.
Apply the identical linear operator to every nuisance Jacobian column.

Check direct marginal-covariance agreement, derivative agreement, full-coordinate
permutation invariance, lost rank, unchanged inputs and fail-closed handling of
invalid shapes, axes, covariance and nonfinite arrays. Nineteen deterministic
checks pass using tiny synthetic matrices. This is software verification, not a
new synthetic flight campaign or empirical calibration.

## Saved-parameter diagnostic to freeze next

Prepare an exact inventory of the latest six primary fits for each stretch,
following the qualified result ledgers rather than choosing the smallest costs
from all historical attempts. For each available artifact verify its hash,
parameter point, residual, full Jacobian and receiver layout. Record missing
artifacts without decoding originals or silently substituting another fit.

Before running the diagnostic, freeze its inventory, covariance assumptions,
source/environment hashes, number of projections and factorizations, thread
allocation and no-retry rule. Use full 3D, horizontal-only and height-only
marginals at the same saved parameter points. Report physical component errors,
projected objective and local singular spectrum while retaining all columns.
These fixed-parameter comparisons cannot establish an ablated optimum or
replace the current shape/field dispositions.

## Observed refits require further qualification and their own freeze

The receiver-axis adapter must first reproduce independently generated physical
motion and show honest treatment of rank loss and active bounds. Select a small
development subset using source/geometry coverage, not improvement after ablation.
Freeze each model, both processing cases, initialization, maximum starts,
evaluation budget, diagnostics and required repeats before any observed refit.
All candidates receive the same coordinate subset and uncertainty treatment.

Define altitude dependence precisely: the first horizontal-only objective may
retain heights for initialization, covariance and propagation, and must be named
accordingly. A stronger altitude-independent alternative needs separate choices
for those dependencies. Comparable rules apply to gravity and receiver metrics.

A gyro-free or acceleration-free experiment cannot simply delete a process input
and keep its effects through attitude or initialization. State the replacement
constraints, qualify them independently and report cases where the requested
separation is not identifiable. Never substitute Group-1 fused rates or attitude.

This plan does not authorize another archive-wide refit or change any scientific
threshold. Exact device documentation remains useful supporting work. No free
background field or solar-versus-sidereal fit is started by this development step.

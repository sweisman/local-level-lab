# Turning-route fixed-point numerical probe

## Question and boundary

The sealed four-case generated study stopped at two nonconverged turning
fits. Do their saved final points and the unchanged bounded correction give
repeatable residuals? Does a shorter step along that correction decrease the
actual cost? This is a numerical diagnosis, not a new fit or a model decision.

Only the two generated turning cases are eligible. The sealed
`generated-geometry-calibration-v1-20261117` study supplies their exact fit
points, noise hashes, recipe and completion hashes. The task reconstructs the
same generated training increments and receiver reports, verifies them against
the parent binding, and never reads an original or protected recording or a
later receiver position. The scientific inputs, objective, calibration bounds,
clock, noise law and stopping thresholds are unchanged.

## Finite execution

One task per turning case. Each performs at most ten tangent sweeps: baseline,
exact repeat, the shared full correction and seven declared fractions of that
correction. It starts no optimizer. The shared `stopping_resolution.probe`
records the full residual and Jacobian for every sweep, compares actual and
linearized costs, and preserves the parent convergence labels. Two workers use
one numerical thread each. Native calls and packet visits are prepaid under
the study journal; generated-input construction is charged separately. The
cooperative wall limit is 20 minutes. No retry or allowance expansion is
authorized for a completed task.

Before launch, source and task-recovery qualification must pass under the
guarded two-thread environment. The frozen definition includes this plan,
the exact source closure, environment, parent completion and fit hashes, task
identities and finite limits. A failure remains saved. Reboot resume verifies
the journal, leases, hashes and charges and schedules only unfinished tasks.

## Interpretation

The result can identify repeatability, local model error or a cost decrease
along the saved correction. It cannot by itself qualify a new solver or
establish aircraft error-law coverage. The two original turning fits remain
nonconverged regardless of this diagnostic. A separate solver qualification
would need independently generated known-optimum controls and a new finite
allowance before any larger motion comparison.

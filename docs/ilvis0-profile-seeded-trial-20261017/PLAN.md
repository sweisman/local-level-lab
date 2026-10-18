# Profile-seeded free-time qualification

## Method and scope

The completed five-offset profile for stretch `50f24131843071ae9312c082` showed
repeatable nuisance fits but a nonmonotonic cost as timing changed. This trial
uses the complete, sealed five-point grid to choose a starting solution, then
releases time and fits every original active parameter under its original bounds.
The grid changes initialization only, not the observation model or final gate.

Run the zero-field-globe, unsubtracted-processing target twice. For each run,
use the five profile fits descended from that run's own original nuisance start.
Require all five points and their within-offset repeat checks to pass; do not
silently drop failed or higher-cost points. Choose the smallest saved cost,
breaking an exact tie by normalized time. These are two numerical repetitions
on one recording, not independent scientific observations.

## Software qualification

One sealed batch of 24 checks, at most 4,096 software callbacks and 120 seconds,
with four total numerical threads and no archival originals or observed calls.
Known-answer controls include a worse local minimum that passes the existing
solver gate, a better well reached through the timing grid, interior and boundary
optima, restoration of the free timing dimension, incomplete/mismatched evidence,
native failures, real receipt accounting and full-time repeat comparisons.
The existing solver, bounds and stopping tolerances remain unchanged.

## Observed allowance

- Two fresh smooth controls, at most three native diagnostic tangents each;
  compare their costs with their sealed source results at relative 1e-8.
- Two target free-time fits. Per target: one native selected-seed check, at most
  80 native solver calls including its fresh stopping checks, then at most three
  independent full-dimensional diagnostic calls.
- **Four charged identities, two optimizer starts, 174 native calls maximum**,
  four total numerical threads, no retries. No new conditional grid fits.

Freeze source/input/original hashes, exact seeds/grid, complete task identities,
environment and limits before launch. Charge every start/call before execution.
Interrupted work stays charged; do not retry an identity or expand allowance.
Completed work cannot restart. Reused profile fits and prior failures retain their
original labels and receipts. A failure of either fresh control blocks targets.

## Required checks

Fresh selected-seed cost must reproduce its saved value within relative 1e-8.
The free fit uses all original columns, including time, and must pass the existing
fresh position/cost/stationarity gate. Independently repeat the final native
evaluation and the same full-dimensional gate. Preserve the complete residual,
Jacobian, timing parameter, receiver epochs and final cost. Final cost must
reproduce the solver output within relative 1e-8 and must not materially increase
from the selected seed.

Both target fits must converge and agree at the existing relative 1e-6 cost and
1 cm axis track-RMS repeat limits. Different final time offsets are permitted
only if the existing full checks and prediction repeatability all pass.
No global optimum is proved by searching five timing seeds.

Publish both controls, both fits, every failure and repeat metrics. A successful
trial still needs saved companion/model checks before any stretch disposition
changes. No wider rollout, changed physical assumptions, calibrated significance
or production promotion follows automatically. The published 49/0/4 findings
remain unchanged until that separate saved-evidence review is complete.

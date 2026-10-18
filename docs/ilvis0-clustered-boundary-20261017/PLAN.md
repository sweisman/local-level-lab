# Search the nearby packet-boundary cluster

## Fixed question and sources

The completed exact-boundary diagnostic preserved two passing controls and two
failed target checks. Each left probe reached a new packet boundary with stable
cost and position while remaining nonstationary. The neighboring boundaries are
about 0.26 ps apart. The final stopping rule is not relaxed to cross that boundary.

Instead, use the existing complete-cluster timing search on the same two source
endpoints. It enumerates representable packet transitions within one microsecond
of the source, seeks a negative-to-positive timing-slope bracket, and applies the
unchanged two-sided stopping check at the selected knot. It makes no global
optimality claim. Search failure or a failed final check remains a failure.

Sources, measurements, nominal clock, bounds, receiver weights, model and processing
case match the previous diagnostic. The interrupted free-time fit is not retried.
Retain both source endpoints and all earlier outcomes.

## Finite limits and controls

- Four fresh diagnostic identities, **58 native calls maximum**, zero nonlinear
  optimizer starts, four total numerical threads and no retries.
- Two smooth controls: three full native tangent calls each.
- Two target endpoints: at most twenty-six full native tangent calls each,
  including the complete-cluster search and final two-sided check.
- At most 402,048 saved-clock queries and six bounded affine solves across the
  controls and target checks. The search window is fixed at one microsecond.
- One software-qualification batch: twelve tests, at most 512 software callbacks,
  120 seconds, no original reads or observed calls. Controls include an initially
  nonstationary cluster edge, maxima, discontinuities, nuisance failure, source
  mismatch, native exceptions, frozen-executor reuse and changed-layout rejection.

Freeze all sources, exact source vectors, inputs, originals, environment, task
identities and limits before launch. Require one GiB free storage before launch
and each identity. Charge every start/call before execution. Interrupted starts
remain charged; do not retry an identity, expand allowance or reuse unused calls.
Completed work cannot restart. Preserve the blocked earlier ledger without repair.

## Unchanged final requirements

Fresh source predictions must reproduce the preserved source under the existing
relative 1e-8 cost, 1 mm axis-RMS and 1 cm epoch-maximum movement limits. Preserve
the original repeat, stationarity and continuity checks on both sides of the final
knot. Check cumulative movement from the saved source to the final selected point.
Keep the full residual, Jacobian, final parameter vector and all search outcomes.

Both controls and both endpoints must pass, with final endpoint predictions
agreeing within relative 1e-6 cost and 1 cm axis track RMS. Publish failures and
complete search traces. A pass requires a separate saved companion/model review
before changing a stretch disposition; no calibrated significance or production
promotion follows. Current findings remain 49/0/4 until that review.

## Executor reuse

The launcher uses a private copy of the previous verified diagnostic executor.
Checked, count-limited substitutions change the helper import, geometry arguments,
study identity, tests and finite limits. The original executor file is unchanged.
Source snapshots contain the original executor, the explicit substitution recipe,
the existing search/stopping code, the new source-preservation wrapper and tests.
The final stopping equations and tolerances are unchanged.

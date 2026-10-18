# Matched two-case free-time test

## Fixed question and source evidence

Stretch `0e73879f98c3b701fd7c42df` has two competing saved alignments in each
processing case. The completed matched fixed-time study reproduced all eight
restricted fits and passed all four within-anchor repeat comparisons. Timing
gradients remain nonzero at some endpoints, so restricted completion alone cannot
resolve the stretch.

This study uses those sealed results, not the interrupted free-time study of a
different stretch. All prior failures and receipts remain unchanged.

## Implementation

`analysis/tests/ilvis0_remaining_free_time_v2_worker.py` privately adapts the
completed profile-seeded executor. Its original source is never edited. The
existing `lll.ilvis0_profile_seeded` candidate and bounded trust solver are reused.
New tests check exact case/start coverage, missing or failed profiles, mixed
layouts, unchanged modules, separate repeat groups and accounting. Existing
known-answer controls exercise free timing, bounds, failure propagation and the
real immutable receipt ledger.

Before launch, seal the successful software qualification, plan, source snapshots,
original-file hashes, saved evidence, native kernel and numerical environment.
Hold exclusive locks on the worker and source study. Every native call is charged
before execution; an incomplete receipt transaction blocks continuation. Charged
starts cannot be retried, and no completed allowance is reused.

## Finite allowance

| Work | Maximum |
|---|---:|
| Fresh smooth controls | 2 identities × 3 diagnostic calls |
| Free-time fits | 4 identities × 81 fitting calls |
| Fresh full checks | 3 diagnostic calls per fit |
| Charged identities | **6** |
| Nonlinear optimizer starts | **4** |
| Native calls | **342** |
| Numerical allocation | **4 total threads**, one worker |
| Retries | **0** |

The 81 fitting calls include one reproduction of the selected saved endpoint and
at most 80 solver calls. At approximately 22 seconds per native call, exhausting
the allowance takes about two hours. Earlier stopping is possible.

## Unchanged physical assumptions

Both cases retain ±1 degree/hour constant gyro offsets and either fixed-zero or
profiled upstream background-field removal. The nominal 200 Hz increment clock,
receiver coordinate weights, selected interval, ±0.15-second alignment bounds,
other physical bounds and zero-field globe model are unchanged. No raw
measurement is interpolated or repaired.

For each case and starting solution, retain both verified profile anchors and
choose the smaller saved objective, with alignment as a deterministic tiebreak.
No result from the other case enters seed selection. Release all original
parameters; do not hold timing fixed during the new optimization.

## Required checks and interpretation

Both fresh controls must pass before target starts. Every target must pass the
existing full stationarity, repeated-center and fresh physical-position stability
checks. Reproduce the selected saved objective and final objective without an
unexplained increase. Save final parameters, residuals, full Jacobian and packet
boundaries for every completed check.

Compare primary and repeat separately within each processing case using the
unchanged relative-cost limit of 10⁻⁶ and 0.01-metre per-axis track RMS. Report
failures as failures, including supported integration-boundary problems. Do not
replace smooth full-space checks with relaxed tolerances.

Even a successful trial requires a separate saved companion/model review before
changing a published disposition. All six primary model fits, fresh controls and
required repeat agreements remain necessary. No global optimality, calibrated
significance, processing provenance or causal interpretation follows from this
numerical test. The other two unresolved stretches are outside its allowance.

Shared source directories acquire one exclusive lock each. The earlier preparation
remains preserved with zero charged starts and zero native calls; its duplicate-lock
startup failure cannot be resumed. This separately frozen launcher changes lock
handling only and retains the same finite scientific scope.

# Matched source-preserving timing-boundary diagnostic

## Frozen question and sources

Check all four completed free-time endpoints of stretch
`0e73879f98c3b701fd7c42df`, zero-field globe, under `bias1_unsubtracted` and
`bias1_profiled_removal`, primary and repeat. Reuse their exact final parameter
vectors and hashed residual/Jacobian artifacts. Include the same two smooth
controls, checked afresh. The prior study completed 198 native calls; it cannot
resume or lend its unused allowance to this study.

The completed saved-only audit used four endpoints and 1,336 clock-geometry
queries, without native calls or original reads. It found a timing-only
stationarity failure without removal and a fresh cost/stationarity correction
failure with profiled removal. Both are near integration boundaries. This new
diagnostic tests the same local-boundary explanation across both mechanisms;
failure under either case remains a failure.

## Implementation and software qualification

`analysis/tests/ilvis0_remaining_boundary_worker.py` privately adapts the completed
clustered-boundary executor. Checked substitutions change identities, source
selection, finite limits, source locking and case-separated comparison. The old
executor, search helper, numerical engine and stopping equations stay unchanged.

The existing `lll.ilvis0_clustered_boundary.check_endpoint` reproduces the saved
source first, searches representable transitions within one microsecond, and
seeks a negative-to-positive timing-slope bracket. Its final two-sided check
includes permitted nuisance corrections. Final predictions must remain within
the unchanged source-to-final movement limits. A failed search, unsupported probe
or failed nuisance correction cannot qualify the endpoint.

One bounded qualification batch contains 18 tests, at most 512 software callbacks
and a 120-second timeout, with zero original reads or observed calls. Tests cover
successful cluster recovery, maxima, discontinuities, unfinished nuisance steps,
source mismatch, charged native exceptions, exact source population, layout and
time changes, unique real locks, completed-template isolation and separate
primary/repeat comparison under the two processing assumptions.

## Finite numerical allowance

| Item | Limit |
|---|---:|
| Fresh smooth controls | 2 identities × 3 native calls |
| Target endpoint checks | 4 identities × 26 native calls |
| Charged diagnostic identities | **6** |
| Total native calls | **110** |
| Nonlinear optimizer starts | **0** |
| Saved-clock geometry queries | **804,096 maximum** |
| Bounded affine correction solves | **10 maximum** |
| Timing search window | **1 microsecond** around each source |
| Numerical allocation | **4 total threads**, one worker |
| Retries | **0** |

Each target allows at most 200,000 transition queries and 1,024 final-bracket
queries. Its 26-call cap includes source reproduction, repeated source, timing
search, final relocation and the full two-sided check. The per-identity receipt
guard prevents borrowing calls. Exhausting 110 calls takes about 50 minutes at
recent speed; earlier stopping is possible.

Freeze exact identities, qualified source snapshots, selected intervals, source
artifacts, original hashes, environment, native kernel and this plan before
launch. Require one GiB free storage. Hold one exclusive lock per distinct
source directory. Charge every identity and native call before execution;
incomplete receipt transactions block continuation. Never retry a charged identity,
restart a completed study or enlarge its allowance.

## Unchanged physical and acceptance rules

Keep measurements, receiver weights, nominal 200 Hz increment clock, original
parameter bounds, ±1 degree/hour constant gyro offsets and the two processing
assumptions. Do not change a model or add time-varying calibration freedom.

Both fresh controls must pass before targets. Source predictions and cumulative
movement retain the existing relative-cost, millimetre axis-RMS and centimetre
epoch-maximum limits. Keep the full stationarity, continuity, repeated-center
and two-sided nuisance checks at the chosen boundary. A local sign change is
insufficient by itself. Save final vectors, residuals, Jacobians and complete
search outcomes, including failures.

Compare primary and repeat separately within each processing case, at the same
observation epochs, using relative objective difference at most 10⁻⁶ and axis
track RMS at most 0.01 metre. A pass in one case cannot compensate for failure in
the other. Publication records every charged identity and outcome.

Even an entirely successful diagnostic needs a separate saved companion/model
review before changing the public tally. This plan does not authorize another
recording, a retry, altered stopping rules, a scientific detection threshold or
a corpus-wide run. Current findings remain 50/0/3.

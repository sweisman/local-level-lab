# Qualification and finite representable-boundary diagnostic

## Numerical question

The completed boundary study used 82 native calls and passed both controls and
both profiled-removal endpoints. Its two unsubtracted endpoints found a timing
slope change but stopped at the minimum spacing guard. Their saved side points
are distinct and match their intended clock states. The audit used twelve
saved-clock queries, no native predictions and no original IMU data.

This candidate changes the geometry qualification, not the scientific stopping
limits. It must not simply disable the guard or accept any slope change. It
checks explicit interval membership, distinct floating-point values, an
eight-ULP parameter margin, distinct adjacent clock states and agreement of all
four side points with those states. An ULP is one representable floating-point
spacing at the parameter value.

## Implementation

`lll.ilvis0_representable_boundary` executes private copies of the existing
adapter, source-preserving wrapper and two-sided stopping code. One checked
substitution replaces the fixed absolute minimum spacing with the direct
representability rule. Cost, stationarity, position, continuity, bounded affine
corrections, source-to-final movement and repeat equations stay unchanged. Frozen
helpers and earlier results are never edited.

The direct clock check reserves six of the existing 1,024 geometry queries; the
transition enumerator retains its 200,000-query cap. Search remains within one
microsecond, with at most twelve derivative evaluations and 26 total native calls
per target. A failed or collapsed interval, wrong clock state, unsupported
correction or unstable native prediction remains a failure.

`analysis/tests/ilvis0_representable_worker.py` uses a private instance of the
previous diagnostic executor. It selects only the exact two audited unsubtracted
sources and two passing controls. The profiled-removal pair must already have
passed its original checks and repeat comparison before preparation is permitted.
It is sealed as prior evidence rather than rerun.

## Frozen software qualification

One 31-test batch, a 120-second timeout, at most 1,024 software callbacks,
81 compiled-motion calls and six compiled clock comparisons. Four total threads;
zero original archive reads or observed calls. Freeze sources and the finite
software allowance before running it. Preserve any failed batch.

Controls cover narrow and broad known minima, maxima, discontinuities, nuisance
failures, collapsed/under-resolved branches, invalid partitions, wrong clock
states, budget exhaustion, source mismatch, charged native errors, nonfinite
values, unchanged frozen modules, exact task scope and repeat agreement. An
independent compiled packet-clock comparison checks all side states. Three
compiled increment-integration controls use independently specified straight
trajectories and test observation agreement at the declared physical resolution.

The motion controls do not demand nanosecond recovery of a time parameter when
its position effect is below the existing millimetre stopping resolution. They
require the accepted predicted observations themselves to agree with the
independent analytic track. This is not a demonstration of precise timing,
instrument calibration or observational confidence coverage.

## Observed diagnostic allowance, only after qualification

| Item | Maximum |
|---|---:|
| Smooth controls | 2 identities × 3 native calls |
| Unsubtracted primary/repeat endpoints | 2 identities × 26 native calls |
| Charged identities | **4** |
| Native calls | **58** |
| Nonlinear optimizer starts | **0** |
| Clock-geometry queries | **402,048** |
| Bounded affine correction solves | **6** |
| Total numerical threads | **4**, one worker |
| Retries | **0** |

The target is stretch `0e73879f98c3b701fd7c42df`, zero-field globe,
`bias1_unsubtracted`, primary and repeat. Use each completed source's full
parameter vector and hash-checked residual/Jacobian artifact, not an interrupted
identity. Keep the selected interval, original measurements, receiver weights,
nominal 200 Hz clock, physical bounds and model unchanged.

Seal exact tasks, qualified sources, this plan, original hashes, saved artifacts,
kernel and numerical environment before launch. Hold one lock per distinct source
directory, require one GiB free storage, charge calls before execution and retain
failures. An incomplete transaction blocks continuation. Never restart completed
work, retry a charged identity or reuse an older study's unused allowance.

Both fresh controls must pass first. Each target must pass source reproduction,
the revised explicit geometry check and the unchanged full two-sided native
checks. Cumulative movement from the saved source must pass. The endpoints must
agree within relative objective difference 10⁻⁶ and per-axis track RMS 0.01 m.
Report all outcomes and search traces.

Even a complete pass requires a separate saved companion/model review covering
both processing assumptions and all three physical candidates. No label change,
threshold calibration, wider corpus run or causal rotation claim follows from
this diagnostic alone. Current published findings remain 50/0/3.

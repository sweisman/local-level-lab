# Matched time-alignment profiles for an unresolved stretch

The saved fits for stretch `0e73879f98c3b701fd7c42df` disagree on the time
alignment between IMU increments and receiver positions. The zero-field globe
offsets differ by about 17.3 milliseconds without upstream field removal and
70.0 milliseconds when removal is fitted. Timing changes can be partly absorbed
by initial-position, acceleration and other permitted calibration adjustments.

This diagnostic holds each of those four exact saved offsets fixed and fits all
other active parameters twice: from the saved primary solution and from its
saved repeat. Both processing cases are included. Two fresh smooth controls run
first; failed controls prevent target starts.

## Implementation and checks

- `analysis/tests/ilvis0_remaining_time_profile_worker.py` prepares, freezes and
  runs the new study. It privately adapts the completed fixed-time executor;
  that executor and its studies remain unchanged.
- `analysis/tests/test_ilvis0_remaining_time_profile_worker.py` checks both
  processing cases, both starts, the already-passing source repeat, exact
  offsets, parameter order, invalid populations and template isolation.
- The existing `lll.ilvis0_fixed_time_profile.FixedTimeProblem` and bounded trust
  solver retain their physical bounds and stopping tolerances. Existing adapter
  controls include three compiled-motion known-answer cases.
- The fresh full-Jacobian diagnostic uses the receipt ledger's supported
  `tangent` call kind. The earlier study's accounting failure remains recorded.
- Final artifacts retain full parameters, residuals, Jacobians, timing
  derivative, observation epochs and receiver geometry. Raw source hashes,
  extraction provenance, source snapshots and environment are checked.

## Finite scope

| Item | Limit |
|---|---:|
| Fresh smooth controls | 2 identities × 3 native calls |
| Conditional nuisance fits | 8 identities × 80 fitting calls |
| Final full-Jacobian diagnostics | 1 per nuisance fit |
| Total charged identities | 10 |
| Total native calls | **654 maximum** |
| Saved within-anchor comparisons | 4 |
| Numerical threads | **4 total**, one worker |
| Retries | **0** |

At the recent rate of approximately 22 seconds per native call, exhausting the
allowance would take about four hours. A conditional fit can stop much earlier.
No completed allowance is reused or extended. Interrupted identities remain
charged; incomplete receipt transactions block resumption.

## Required interpretation

Report every offset, both starts and every failure. At each common fixed offset,
compare conditional completion, relative objective difference and reconstructed
track agreement under the existing 10⁻⁶ cost / 0.01 m axis-RMS limits.

Fixed-time completion does not demonstrate free-time convergence. These results
cannot change the public shape tally. Any later full comparison must pass its
original primary, repeat and companion requirements under a separate finite
freeze. Measurements, selected interval, candidate models, receiver weights,
nominal integration clock and physical bounds remain unchanged.

The other two unresolved stretches retain their separate timing/calibration
diagnoses. This study neither expands to them nor starts an Earth-model campaign.

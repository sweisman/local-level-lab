# Software 0.6.0 validation and publication boundary

The correctness release preserves the physical model, provenance architecture, raw schemas 2/3
and WMM sensitivity check. Dynamic crab, noise weighting, bootstrap dependence, forward-axis
uncertainty and pooled significance remain research questions. Real slow-rate bench evidence and
demonstrated false-rejection tails remain publication blockers after these software corrections.

## Regression checks

Verified on 2026-10-04 with the pinned Python 3.14 dependencies and JDK 21:
130 analysis tests, 12 server tests and 14 Android unit tests passed; `lintDebug` and
`assembleDebug` passed. Server tests required execution outside the sandbox because its
cross-thread asyncio calls stalled. The final analysis suite took about six minutes.

`pytest analysis/tests/test_release060.py analysis/tests/test_policy.py` exercises short/dense GNSS,
identical/conflicting timestamps, missing-turn integration at 20/100 Hz, heading permutations,
free/fixed nonlinear MAP reference solutions with nonzero crab and 5°/15° priors, nonconvergence,
direct and seeded Gaussian covariance propagation, empirical bootstrap covariance and migration.
Android unit tests cover delayed recovery and stop cancellation, deterministic packaging, pending
upload identity, retry retention and terminal cleanup without losing acknowledgement. Real process
death and Bluetooth recovery on both physical IMUs remain part of BENCH.md.

## Seeded experiments

The opt-in `analysis/tests/research.py` harness records the software, policy, environment, seed,
scenario, sampling method, block length, per-run failures and runtime. The synthetic sensor's
rotation is differentiated from its attitude matrices; the fitting correction is not used to
generate dynamic crab. Constant per-leg crab inputs remain supported.

```sh
PYTHONPATH=analysis:server python analysis/tests/research.py --scenario drift+1 --truth all --seeds 1 --sampling moving --blocks 15 --bootstrap 20 -o docs/pilot-060.json
PYTHONPATH=analysis:server python analysis/tests/research.py --scenario pool --truth all --seeds 1 --units 2 3 5 10 -o docs/pool-pilot-060.json
```

Estimate larger campaigns from the pilot wall time and obtain approval before running them.
`--scenario all --truth all` covers within-leg crab 0, ±0.5, ±1, ±2, ±5°/h, smooth shifts,
finite-duration transitions, anisotropic/correlated gyro noise, routes at different latitudes,
dateline crossings, turn dropouts, thermal ramps, long-period bias and combined hardware faults.
Repeat with `--variant ble` as well as `spp`. `--sampling moving segment --blocks 5 15 30` compares
current moving blocks with experimental blocks restricted to contiguous segments. Exports include
empirical and current joint covariance, their eigenvalues and joint 95% coverage. Empirical
bootstrap covariance never replaces the production matrix automatically. Bootstrap refits still
use the local linearization, with a prior on the total crab angle.

Results stay separate by truth, scenario, sampling and block length. Each group reports attempted
runs, analysis failures, eligibility exclusions, accepted runs, unconditional false rejection among
analyzed runs, rejection conditional on acceptance, and the complete gated decision rate among
attempts. Every binomial rate includes a Clopper–Pearson interval. Simulation explicitly assumes
approved provenance and a usable bench certificate; all remaining primary gates still apply.
It cannot establish actual physical provenance or hardware qualification.

Summary-level pooling uses known correlated unit effects, repeated observations per unit, unequal
covariances and varying unit counts. Closed-form independent univariate reference fixtures live in
`analysis/tests/pooling_reference.json`. These small checks are not tail calibration or a validation
of the general multivariate pooling approximation.

## Hardware and publication sequence

### Small pilot, 0.6.0

[Flight pilot](pilot-060.json): one seed per truth at +1°/h within-leg crab, moving blocks of 15
bins and 20 bootstrap replicates. All three analyses converged and retained their true model;
all three were excluded by primary gates (prior sensitivity, and additionally WMM selection
sensitivity for the still globe). There are **zero accepted runs**, so this pilot says nothing
about accepted-flight false-rejection tails. Runtime was about 26 seconds on the recorded environment.

[Pooling pilot](pool-pilot-060.json): one seed per truth at 2, 3, 5 and 10 units, with correlated
unit effects and unequal session covariance. No true-model rejections in these 12 summaries;
two-unit results are exploratory. This is a runtime/functional check, not a tail study.

Two historical regression assertions required the still-world fixtures to reject the rotating
globe. The corrected total-angle objective changes the fixed-model fits and conservative bootstrap
calibration enough that they no longer do so. Correctness tests retain true-model coverage, require
valid nested objectives and compare free/fixed MAP fits with an independent optimizer. Rejection
power must be reassessed using the harness; no noise floor or significance threshold was tuned to
restore those historical assertions.

## Publication sequence

1. Characterize two physical units across axes, signs, slow rates, temperature, orientation and
   power cycles. Estimate scale/misalignment and g-sensitivity matrices with uncertainty; retain raw evidence.
2. Compare constrained time-varying crab, axis/segment noise weighting, segment-aware bootstrap,
   anisotropic calibration magnitude inference and forward-axis uncertainty propagation.
3. Inject known signals into retained real hardware residual series. Simultaneous dual-IMU
   recordings share a flight and cannot be treated as independent flights.
4. Pilot runtime, preregister the required tail precision, then separately approve single-flight
   and pooled campaigns large enough to measure the false-rejection tails with uncertainty.
5. Select production methods and priors from that evidence, publish it and freeze the methodology
   before making primary scientific claims.

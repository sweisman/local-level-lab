# Whole-period prediction coverage: implementation plan

**Goal:** Check whether a two-law, training-only aircraft forecast contains
*every* later coordinate of both the physical track and a separate receiver
report on independent generated recordings.

**Boundary:** This is a generated-data method study. It does not inspect NASA
or protected ESA measurements, establish an observed-aircraft error law, or
compare Earth models on real data.

## Design and decision rule

The [24-recording precursor](../prediction-paired-bound-family/RESULT.md)
qualified the matched-fit data path. Its per-coordinate intervals covered all
later values in that small matrix, but it did not have a whole-period coverage
rule. Use the existing affine whole-forecast wrapper and the two-law union,
with no choice of law from a nearly tied training score.

Predeclare 96 independent recording seeds. For each seed, draw one of the 24
equally weighted combinations of three generated Earth candidates, two
upstream-processing cases, two generating IMU error laws and two calibration
cases. Freeze every draw and seed before fitting. The previous 24-case matrix
already checks each combination; this new cohort tests average performance
over the declared equal-weight mixture. Reuse the two-minute, 300 Hz,
119-receiver-epoch protocol, header-elapsed clock, physical bounds, one start
and 200 evaluations per candidate-law fit. Both fits receive identical earlier
IMU and receiver measurements; later physical truth and later receiver reports
remain closed until the two unions are saved.

For each of the two targets, allocate failure probability 0.025: 0.0125 to
the calibration ellipsoid and 0.0125 across all later coordinates by a union
bound. Thus the **joint** affine lower bound for both targets is 0.95 when one
supplied Gaussian law is correct, true calibration lies in its box and the
linearization applies. The nonlinear generated study measures whether those
conditions suffice in the complete pipeline; the analytic lower bound alone
does not certify it.

Count a recording as a success only if both fits pass the original numerical
and physical screens, both complete interval unions were saved before truth,
and **all** later coordinates of both targets fall inside them. Count every
other generated recording as a failure, including missing results and
technical errors. The cohort passes its preregistered average-failure gate
only with at most one failure among all 96. For 96 independent draws from the
declared mixture, the exact one-sided 95% binomial upper failure bound is
4.85% with one failure (3.07% with none). Report every condition and target
separately, but do not claim a per-condition 5% bound from four or fewer cases.
Preserve abstention for every Earth-model decision.

## Files and gates

1. Add a small paired native adapter in `analysis/lll/` that calls the existing
   training and whole-forecast bound components. Add a law-family union that
   checks identical earlier measurements, target, operator and future time
   grid before opening later truth. Test tampered bindings and target swaps.
2. Add a `lll.studies` definition/evaluator with the frozen 96 identities,
   independent seeds, finite per-task native and construction limits, source
   closure, environment hash, four workers of one thread each and an eight-hour
   cooperative wall cap. Qualify task-level reboot recovery before launch.
   Preserve all completed failures and charges. Do not restart a sealed task.
3. Run one short real-native integration control for both targets and both laws.
   Check saved-artifact order and unchanged earlier inputs; its two-second fit
   may abstain on numerical stopping. The 96-case study must separately report
   numerical stopping and physical screens. If integration fails, diagnose
   before the 96-case run.
4. Launch the finite cohort only after source-bound software and recovery
   checks pass. The estimated cost is roughly six wall-clock hours on four
   cores, based on the 24-case precursor; the frozen wall cap is
   eight hours. The per-recording ceilings remain 479,632 native calls and
   3,012,102,024 packet visits. Keep at least 35 GiB free.
5. Add a saved-only reporter that verifies original and any continuation
   receipts, replays interval containment against sealed withheld truth and
   reports recording-level failures, target-specific counts, widths,
   numerical stops and exact confidence bound. Update the public study index,
   roadmap and next-step page after verification. A failed gate remains failed;
   it blocks the observed-aircraft coverage claim but leaves saved-data
   diagnosis available.

The 96-case result, even if it passes, supports only this generated mixture and
supplied error family. Testing actual aircraft requires a separate frozen
development check and independent flight-group confirmation.

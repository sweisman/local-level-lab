# Fresh calibration and independent validation

The [optimizer qualification](compensated-optimizer-qualification/INTERPRETATION.md)
passes all 48 development fits, all 24 paired-start comparisons and four original
input/error replays. This plan defines the next release; it does not reopen the
earlier campaign or reuse its unused allowance.

## Question and scope

Can the corrected, earlier-only prediction procedure provide a reproducible
error threshold on its declared generated population, then meet the independently
specified validation target on new noise families?

This is **two-minute generated-data calibration**. The trajectories, noise laws
and calibration fixtures are development assumptions. A successful result would
not establish the actual instruments' error law, twenty-minute flight coverage,
or statistical significance for the 53 archival stretches. Those remain separate
scientific gates before reserved aircraft confirmation.

## Unchanged procedure

Retain the qualified compensated mean integration and feasible timing derivative,
original noise propagation, full 26/27-column fits, calibration bounds, two
prescribed starts, 200-evaluation limit, earlier-only initialization, continuous
forecast and physical accuracy screens. No retries or extra starts are allowed.

Each noise family contains all three generating physical candidates, both
processing assumptions, both input-error formats and both starts: 24 fits.
Use the existing training-cost selection between available starts. Preserve
unavailable settings and aggregate the complete family before calibration or
validation. Later physical truth is used only after the forecast is saved.

The mean arithmetic and all scientific/configuration/environment hashes must
match across calibration and validation. Freeze the complete shared method
before calibration; public summaries may change, frozen dependencies may not.

## Separate cohorts and finite allowances

| Phase | New seed families | Maximum fits | Cooperative ceiling |
|---|---:|---:|---:|
| Calibration | 299 | 7,176 | 120 hours |
| Independent validation | 181 | 4,344 | 72 hours |

Calibration seeds are integers 281474977010656 through 281474977010954.
Validation seeds are 281474977110656 through 281474977110836.
Exclude all earlier calibration, validation and development identities. Neither
cohort is a continuation of the stopped campaign, and validation cannot supply
method-development examples.

Use four workers with one numerical thread each, with no other numerical jobs
unless capacity has been released. Charge starts and all native/construction
allowances before execution. Preserve interrupted and failed starts. Never
extend either ceiling, recycle unused allowance or signal workers at a deadline.

The completed 48-fit qualification took 30.3 minutes. A simple proportional
estimate is **about 75 hours for calibration and 46 hours for validation**;
this is a planning estimate, not a guaranteed runtime. The second phase runs
only after the first supplies a finite, audited threshold.

## Fixed statistical gates

Reuse the existing family-score and exact order-statistic implementation:

- Calibration uses the maximum of 299 independent family scores, targeting
  99% coverage with 95% confidence for this generated population.
- Validation targets 95% family coverage with 95% confidence and permits at
  most four failed families in 181. Retain its existing exact calculation.
- If both starts fail any required calibration setting, stop cooperatively:
  the threshold cannot become finite. Stop validation at its fifth failed
  family. Never drop a difficult setting or use a partial cohort to pass.
- A failed or incomplete phase remains failed or incomplete. Validation is
  blocked without a finite, closed, source/environment-matched handoff.

These targets concern prediction error under the declared generated population.
They do not calibrate the minimum-over-globe-models decision on actual flights.

## Shared implementation

1. Generalize the existing calibration executor and closed-result reporter with
   an explicit trusted protocol/provider interface. Preserve their original
   defaults and source-bound historical replay.
2. Add one small compensated-release definition: new cohorts and population
   identity, the qualified native provider, original family selection/stop rules,
   and shared lifecycle preparation. Do not copy the campaign worker or scoring
   algorithms.
3. Qualify cohort separation, complete task counts, population/source/environment
   identity, original-default compatibility, failure charging, early stopping,
   native-cache provenance and the calibration-to-validation handoff. Reuse the
   closed 48-fit qualification; do not rerun it.
4. Prepare and audit a fresh source/input/environment freeze before launch.
   Keep both cohorts and the handoff policy fixed. A software qualification
   failure blocks launch.
5. Publish all outcomes and complete CSV inventories, audit hashes and journals,
   compact evidence through the shared archive, and update the public roadmap,
   study index and concise overview after each verified phase.

## After this release

Record whether the generated-data gate passes and exactly which population it
covers. Keep the original 53-stretch evidence and every earlier failure intact.
Assess applicability to longer recordings and actual measurement errors before
opening reserved ESA groups or claiming calibrated flight-level evidence.
Failure does not authorize another campaign or an expansion of these allowances.

[Roadmap](ANALYSIS_ROADMAP.md) · [Earlier closed phase](PREDICTION_PHASE_RESULTS.md) ·
[Prediction protocol](PREDICTION_VALIDATION.md).

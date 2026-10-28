# Fresh prediction calibration with qualified timing checks

This defines a separate finite release. The
[48-case optimizer qualification](timing-local-matrix/INTERPRETATION.md)
passes all fits, 24 paired-start comparisons and four original input replays.
Both earlier calibration campaigns and their unused allowances remain closed.

## Question

Can the qualified training-and-prediction method produce a finite error threshold
on new generated examples, then meet its fixed coverage target on a separate
cohort? These are two-minute simulated measurements with declared noise and
calibration settings. Actual aircraft error laws and longer-record coverage
remain separate requirements.

## Method stays fixed

Retain compensated coordinates, local timing-cell verification, the original
noise propagation and physical parameter bounds. Keep both input formats,
all three generating candidates, both processing settings and two prescribed
starts: 24 fits per independent noise family. Retain every 26/27-column nuisance
configuration, the 200-evaluation limit, 620-operation linear-work limit and
all numerical and physical forecast screens. No extra starts or retries.

Choose between available starts by training cost alone. Aggregate each complete
family before scoring it. Save forecasts before consulting later truth. A
missing required setting prevents a finite calibration threshold; it cannot be
silently removed. Preserve the existing cooperative failure rules.

## Proposed separate cohorts and limits

| Phase | New independent families | Maximum fits | Runtime estimate | Proposed cooperative ceiling |
|---|---:|---:|---:|---:|
| Calibration | 299 | 7,176 | About 164 hours | 240 hours |
| Independent validation | 181 | 4,344 | About 99 hours | 144 hours |

The estimates scale the measured 65.7-minute qualification run. They are planning
estimates, not performance guarantees. The earlier 120/72-hour ceilings belong
to closed releases and cannot be extended or reused. This proposed release
requires its own reviewed compute allowance before launch.

Calibration seeds: 281474977210656–281474977210954.
Validation seeds: 281474977310656–281474977310836.
Before freezing, verify separation from every earlier declared calibration,
validation, development and reserved family. Exclude earlier cohorts even where
their fits were never executed. Preserve the new cohorts without examining
validation outcomes during development.

Use four workers with one numerical thread each, at most two native builds per
worker and the shared deterministic task and prepayment formulas. Derive and
verify exact native-call and packet-visit totals before preparation. Charge work
before execution, retain interrupted starts and close unused work when a phase
ends. Keep calibration and validation source, configuration and numerical
environment identical; freeze both policies before calibration starts.

Allow at least **55 GiB free before calibration** and **35 GiB before
validation**. The release launcher checks this before starting a worker or
charging a fit. The completed controls suggest about 15–20 GiB of uncompressed
case artifacts for calibration and 9–12 GiB for validation. Publication can
temporarily duplicate them. Verify, archive and compact calibration before
starting validation. These estimates allow headroom; they do not guarantee
storage use for every possible outcome.

## Statistical gates stay fixed

- Calibration uses the maximum of 299 independent family scores to target
  99% coverage with 95% confidence on the declared generated population.
- Independent validation targets 95% family coverage with 95% confidence:
  at most four failed families among 181, using the existing exact calculation.
- If both starts fail a required calibration setting, stop cooperatively.
  Stop validation at its fifth failed family. Keep every failed outcome.
- Validation needs a finite, audited handoff from the entire calibration cohort.
  A partial cohort, changed method or changed environment cannot supply it.

These targets calibrate generated prediction errors. They do not establish the
significance of the minimum-over-globe-models decision on aircraft observations.

## Shared implementation and readiness checks

The shared runner uses a counted solver scope that finishes validation before
scoring or family selection. The closed-result reporter independently checks
method-specific evidence while preserving saved fit labels. A small release
policy supplies the separate cohorts, method binding and resource preflight.
Source-bound qualification and a fresh execution freeze are required before
either phase launches.

Reuse the existing campaign executor, family scoring, closed-result reporter
and calibration handoff. Add a small release definition and an explicit timing
solver provider, with per-fit linear-work journaling. Preserve the original
defaults and archived replay; do not copy a campaign worker.

Require source-bound tests for cohort separation, complete task counts,
population/source/environment identity, provider forwarding, charges preserved
after failure, cooperative stops and the handoff. Independently audit every
returned timing check with the correct parameter count and saved work journal.
Bind the completed matrix's exact hashes and unchanged numerical method bodies.
Prepare a fresh source/input/environment freeze only after the software passes.

Publish all planned rows and returned outcomes, including failures. Packaging
must never refit. Verify receipt hashes and archived replay, compact evidence
through the shared store and update the public roadmap at each milestone.
Protected ESA groups, original measurements and the 53-stretch findings remain
unchanged.

[Current roadmap](ANALYSIS_ROADMAP.md) · [Next analyses](NEXT_STEPS.md) ·
[Previous closed release](prediction-calibration-compensated/INTERPRETATION.md).

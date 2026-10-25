# Fresh-draw fitting and prediction pilot

This is a generated-data diagnostic of the complete fitting procedure. It does
not open another aircraft interval or a reserved ESA group. The
[saved-score study](../fitted-prediction-scores/INTERPRETATION.md) and every
earlier failed numerical or accuracy check remain unchanged.

## Fixed question and matrix

Repeat the existing two-minute noisy training/prediction procedure with two
preassigned fresh seeds: **26102610** and **26102611**. Their role is
`method_diagnostic_pilot`; they cannot later estimate a calibration threshold or
serve as independent validation. Software seed checks use different seeds.

For each seed retain both input-error formats, all three generating/fitted
candidates, both processing assumptions and both declared starts. This makes
48 starts. Each candidate is fitted to data generated under that same candidate;
this is not a three-way Earth-model comparison.

Preserve 300 Hz sampling, 120 seconds, 119 receiver epochs, the first 79 epochs
for training, the original calibration bounds and the 200-evaluation limit per
start. Keep the original 10 m horizontal / 30 m height descriptive screen.
Estimate calibration anew from earlier observations; never supply true initial
state, true calibration or later positions to fitting or weights. Save forecasts
before later truth. Use training cost and declared order for primary selection.

## Qualification before launch

The seed interface must pass its frozen-generator compatibility checks.
Extract the existing `structured_noisy_study.evaluate` execution body into one
shared case runner, preserving its prepayment, construction journal, native
factory and failure handling. Keep the original evaluator as its strict caller.
The new small `lll.independent_noisy_study` definition calls that runner and the
shared prediction scorer; it must not copy a worker or navigation library.

Qualify lifecycle binding, immutable seed identity and retained failed outcomes.
Reuse the twelve short native protocol controls at the separate qualification
seed **26102602**, including both formats and all model/processing cases. Add
the score check to the real saved forecast path. The short native qualification
keeps its existing 1,000-call / 10,000-step / 30,000-query-visit limits per case,
eight fit evaluations, two shared libraries and five-minute cooperative ceiling.
Its purpose is correct execution and honest labels, not a positive confidence claim.

## Separate finite allowance

Use two workers with one numerical thread each, reserving two threads while the
existing full test job owns its allocation. Expect roughly two hours at the
earlier measured throughput; the new cooperative ceiling is **four hours**.
Do not terminate a process to enforce it. No retry or reuse of another study's
unused allowance is permitted.

| Resource | Per start | Complete 48-start allowance |
|---|---:|---:|
| Native calls, including packetwise covariance work | 59,954 | 2,877,792 |
| Conservative packet-query visits | 376,512,753 | 18,072,612,144 |
| Constructed intervals | 36,000 | 1,728,000 |
| Generated samples | 36,199 | 1,737,552 |
| Normal variates, increment law | 648,486 | 15,563,664 for 24 starts |
| Normal variates, rate-point law | 432,492 | 10,379,808 for 24 starts |

Each worker may build the existing noise bridge and wider-tangent library once.
An operator remains capped at 64 MiB. Native counts and visits retain the
existing conservative accounting convention. These are new limits for this
fresh question, not an expansion of the completed study.

## Report every outcome

Retain all source/environment bindings, seeds, raw-input hashes, construction
charges, fit records, error covariances and later error curves. Report numerical
passes and failures separately from physical accuracy and normalized scores.
Select primaries without later errors; retain unavailable groups.

Compute each complete-block coordinate error/noise score with the shared scorer.
The covariance still treats fitted calibration as known. Two new seeds can
expose instability and test the pipeline; they cannot calibrate a rare tail,
establish predictive coverage or validate an Earth-model decision. Further
calibration and validation draws require separate disjoint identities and freezes.

[Independent draws](INDEPENDENT_DRAWS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

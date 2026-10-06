# Next-stage research preparation — 2026-10-06

Both 1,000-attempt pilots are complete. The original preparation used their saved records and
seven observed position tracks without new fits. Subsequent 300-case geometry and 72-case
protocol diagnostics are also complete; neither established a protocol that passes all
required comparisons across both crab models. No fresh calibration or validation has run.
Real IMU testing is pending hardware. The current scientific gate is retained; no production
policy or external-GPS fallback is promoted.

Subsequent [observable-domain enforcement](../flight-domain-development-20261006/README.md)
binds flight thresholds to an explicit route/protocol envelope and acquisition source. It
abstains outside that envelope and rejects calibration/validation domain mismatches. This
software guard does not approve the historical restricted proposal below; its source freeze
is stale, no usable experimental domain has been established, and further execution allowance
remains zero.

The [sharded runner](../sharded-campaigns-20261006/README.md) now implements deterministic
task identities, two single-thread local workers, durable independent journals, interrupted
attempt preservation and streaming duplicate-checked merging. It has software-fixture checks,
including two actual processes; it subsequently completed the initial three-attempt airline
pilot, preserving all three preprocessing failures. Sharded preparation needs a
fresh one-thread environment freeze. These engineering changes do not approve a usable domain,
set decision thresholds or grant additional compute.

A refreshed [airline-route pilot](../airline-pilot-preparation-20261006/README.md) now freezes
18 matched evaluations under the current source and one-thread worker environment.
Its authorized initial three evaluations are complete, all failing before fitting for weak
forward-reference correlation; the remaining 15 are unrun and unapproved. Five archived
paths were reviewed without fits or SVDs; speed/interpolation diagnostics expose assumptions
that need testing. Its three-attempt allowance is exhausted and does not revive older plans.

The saved-data follow-up identifies amplified GPS course noise and artificial bank jumps
from the original position interpolation. Matched smoothing is a research-only forward-reference
diagnostic with no angle uncertainty or flight acceptance. An explicit C2 route alternative
preserves positions and gaps while eliminating bank steps on the selected window. Neither
has run through the complete science fit. The trajectory extension changes the scientific
source freeze, so the completed pilot plan remains historical and cannot be resumed as new work.

The [fresh matched-reference pilot](../matched-airline-pilot-20261006/README.md) now freezes
the opt-in uncertainty-aware method and smoother route with fresh seed 600901. Controlled
checks include continuous small aircraft corrections; covariance treats GPS and gyro jointly
and splits at gaps. Its approved initial three evaluations are complete: all fits converged,
none passed the scientific gate. Only 57 minutes of cruise survived; heading diversity and
every intended design contrast failed. The other 15 remain unrun and unapproved. Coverage,
calibration and independent validation remain pending.

Subsequent geometry-only preflight screened 192 overlapping 75-minute windows across the saved
tracks and 9,640 safe three-turn schedules, with no passing window and one missing-height
failure. Twenty-one longer extensions around the sole no-turn duration/heading pass produced
19 observable-screen passes. The [extended airline pilot](../extended-airline-pilot-20261006/README.md)
uses a 120-minute AUH–ORD window with 25/50/85-minute turns. Its approved three-case prefix
is now complete: all fits converged without analysis failures, retaining 97 cruise minutes
with sufficient heading diversity and a passing forward reference. Every intended design
contrast still failed, with fitted and worst design ranks zero. All pairwise decisions
abstained; the optional mount comparison was unavailable, with no flags or coefficient shifts.
Wall time was about 4m42s. The budget is spent and 15 cases remain unrun. Source and acceptance
gates are unchanged. Diagnose nuisance/contrast losses before another expensive pilot.

That saved-array diagnosis is now [complete](../extended-airline-pilot-20261006/DIAGNOSTIC_REVIEW.md):
smooth bias drift dominates most checked projection losses, and westbound geometry weakens
rotating-globe versus disc separation. Six fixed nominal turn controls do not restore all
contrasts. A course-gap interpolation bug in the analytic design tool is repaired; source
was `a7cc6194...` after that repair; the later shape-rule extension changes it again, so old prospective execution freezes are stale. Completed pilots and
their decisions remain unchanged. Next compare route direction and feasible signal modulation,
keeping the nuisance space, before budgeting a complete-envelope/full-pipeline comparison.

The analysis now also preserves **globe versus the specified disc** as a separate experimental
result when rotation cannot be resolved. It uses the existing gated comparisons; it does not
rescue a route whose globe/disc contrasts fail. The saved first and second pilots give 889 and
900 correct shape preferences, zero incorrect preferences, and 111 and 100 abstentions. These
add 9 and 12 preferences beyond their three-model winners. No new fits or flights ran, and
the composite decision still needs its own error-budget validation.

The geometry tool can explicitly optimize both shape comparisons without requiring rotation
separation. Keep both globe alternatives in that design objective, or declare a single pair
when only that question is intended. Next screen different route directions and safe turn
patterns under these explicit objectives with the same nuisance space.

A potentially useful real airborne source is also [documented for inspection](AIRBORNE_DATA.md).
Its raw IMU archive could support a separate empirical discriminator test after format and
processing checks. The first supplied IPUTI0 measurement sample has now been decoded for
inspection; its status/navigation messages provide no independent raw gyro channels.

The [direction controls](DIRECTION_REVIEW.md) are now complete: 21 fixed patterns, 12 safe,
24 candidate evaluations, including two no-bin failures. Opposite traversal of the longer
route gives a nominal globe/disc pass under physical wind, while rotation remains unresolved.
It still fails under the broader wind correction; no accepted protocol was found.
The NASA inspection has confirmed actual ILVIS0 gyro filenames, a second distinct IPUTI0
source and login redirects on both access paths. An Earthdata account is now available.
The [preserved IPUTI0 sample](airborne-sample-iputi0/README.md) spans about 25½ minutes,
with 1,527 verified packets of each message type and 11 unframed bytes preserved without
repair. Three focused decoder checks passed. The
[subsequent ILVIS0 sample](airborne-sample-ilvis0/README.md) contains 132,444 time-tagged IMU8
packets at approximately 200 Hz over 662.226 s, with GPS in the same log. All 143,471 outer checksums
pass. Timed opaque payloads are preserved, but physical gyro units/axes/corrections still
need documentation. Two focused checks pass; no empirical Earth-model test has been run.

The [remaining plan](PLAN_STATUS.md) separates implemented review features from the geometry,
device qualification and fresh calibration/validation evidence still needed. A 30-state
follow-up preserves the reversed physical-wind shape pass in a small registered subset;
it does not certify the full envelope, and the broader wind candidate still fails.

## Saved-record review and chosen restricted domain

`pilot-comparison.json` compares both pilots under the same 10% rank-margin requirement,
without modifying the original records. They used the same exact trajectory, nuisance-fit
settings and numerical environment. Their source versions and candidate IDs differ and remain
separate; the first pilot's margin review is retrospective, the second's margin was preregistered.

| Pilot | Recorded eligible | Eligible under common 10% margin | Eligible rank 2 | Eligible diagnostic null rejections |
|---|---:|---:|---:|---:|
| First, seeds 600100–600266 | 906 | 894 | 870 | 1 |
| Second, seeds 600300–600466 | 905 | 905 | 884 | 0 |

The first diagnostic rejection is retained. Do not claim that the combined pilots demonstrate
zero false rejection or pool their source versions as independent calibration/validation evidence.
Within each pilot, shared seeds pair the truths and scenarios.

Wind watchdog flags are 132/500 in the first pilot and 120/500 in the second, versus 6/500 and
3/500 under mixed bias, despite zero injected mount creep. Every design-contrast failure has
a watchdog flag: 91 in the first pilot, 72 in the second. The second saves 129 flagged segment
records, including 36 without calibrated airframe-field subtraction; the first lacks those details.
The prior eight-case known-wind oracle establishes crab confounding in those diagnostic cases,
but its simulator heading is unavailable operationally. Keep the protective exclusions; do not
improve apparent acceptance by disabling the watchdog or removing unfavorable records.

The restricted proposed calibration domain remains:

- The exact [75-minute protocol](../development-protocol-75min.json), SPP variant, dynamic crab
  and bias, axis/segment weights, forward-axis uncertainty, 20 nonlinear bootstrap replicates.
- Three model truths × `bias_mixed` and `wind`; the same simulator assumptions as the pilots.
- Model-test rank **2**, a **10%** boundary margin, all intended design contrasts estimable,
  valid convergence/bootstrap and the existing integrity/prior/WMM-selection gates.
- Primary and separate pairwise thresholds, calibrated over all preregistered diagnostic cells.

This defines a restricted simulated benchmark, not an eligible envelope for arbitrary airline
routes or real instruments. Rank-1 evidence remains a development/pairwise diagnostic; this
proposal provides no rank-1 calibrated decision. Broad geometry, combined faults, different
sensors and pooled pairwise summaries need separate review and calibration.

## Prospective geometry stress cases

`geometry-stress-plan.json` selects **24 deterministic synthetic cells** from the 288-cell
matrix. They cover both hemispheres, low/mid/high latitude, two/six headings, poor/good heading
separation, 60/180 minutes, 150/270 m/s, and zero/three/six mount turns. Axis cases plus poor
two-heading/no-turn interactions avoid treating speed alone as measured contrast information.
All 288 schedules now meet the ten-minute spacing/five-minute edge rule: the former 60-minute,
six-turn schedule used eight-minute spacing, and is corrected to 5/15/25/35/45/55 minutes.
That prospective-source fix invalidates old source freezes for future campaigns; completed
evidence retains its original hashes and is not rewritten.

The next proposed design comparison is three truths × two nuisance scenarios × dynamic/wind
crab fits for each selected cell: **288 evaluations**, plus 12 exact-protocol controls if included.
The [300-case diagnostic batch](../geometry-development-20261006/README.md) used fresh development
seed 600500, geometry-only fitting, zero bootstrap and a one-hour cumulative evaluation cap.
It completed with six no-fit records; no geometry passed all comparisons. A saved-record audit
corrected unit-dependent nuisance rank selection, followed by a
[72-case protocol comparison](../protocol-development-20261006/README.md). All 72 fits converged,
but neither protocol passed every comparison. Processing/timing diagnostics remain necessary
before choosing a domain for power and tail work.

Observed cases preserve the position rows, estimate flags and explicitly usable intervals:

| Track | Prospective geometry status | Chosen observed coverage |
|---|---|---:|
| Etihad 10, ORD–AUH | Prepared | 100.0% |
| Etihad 9, AUH–ORD | Prepared | 98.8% |
| AA 1433, ORD–LAX | Prepared | 100.0% |
| FI680, SEA–KEF | Prepared | 100.0% |
| LH572, FRA–JNB | Prepared | 97.5% |
| SQ938, SIN–DPS | Blocked by coverage | Best window 93.4% |
| EK761, DXB–JNB | Blocked by coverage | Best window 68.4% |

Selection uses the largest observed latitude span among 75-minute windows satisfying the
provisional 95% coverage/90-second gap screen. It uses no gyro or inference outcomes. Blocked
tracks remain in the plan, with their gaps/estimates, for coarse inspection. Prepared windows
are not certified cruise or scientific eligibility. Unconfirmed UTC and altitude references
remain explicit; elapsed geometry alone does not align a real IMU recording.

Observed-trajectory replay is now implemented with controlled checks; execution on these tracks
is still pending. [Core-pipeline preparation](../core-pipeline-20261006/README.md) freezes two
explicit modes: original observed fixes, and simulated frequent GPS on an assumed path inside
short observed intervals. Neither bridges long gaps or uses provider estimates as observations.
Mount turns, airframe heading, wind, sensor noise and bias are simulated assumptions.
Original accuracy remains unknown; the frequent-GPS mode has explicitly simulated accuracy.

## Frozen proposal and compute budget

`calibration-proposed-manifest.json` preserves the earlier source, configuration, eligibility and
one-thread numerical environment. It is now **stale**. `readiness.json` records current stage
status and artifact hashes. The original source freeze is historical;
the protocol comparison used a new two-thread environment freeze. Review the final domain and
refreeze before calibration. The historical proposal is not a final validation policy or run permission.

Sample goals remain **29,285 accepted calibration** and **33,169 accepted validation** samples
per truth/scenario cell, with calibration alpha 0.00135, claimed alpha 0.0027, 18-test family,
validation failure budget 64 and planned validation power at least 90% at rate 0.00135.
Development samples cannot substitute for either partition.

`compute-budget.json` uses the latest pilot's rank-2 acceptance and measured runtime, without
pooling historical source versions:

| Planning basis | Calibration attempts/cell | Validation attempts/cell | Combined attempts | Serial days |
|---|---:|---:|---:|---:|
| Point estimate, minimum acceptance 128/166 | 37,979 | 43,017 | 485,976 | 69.0 |
| Conditional attempt reserve | 43,830 | 49,615 | 560,670 | 79.6 |

The reserve uses simultaneous one-sided acceptance bounds across the six cells and
negative-binomial attempt caps across both phases, splitting a 5% planning error allowance
between those stages. Its minimum acceptance input is 0.67456. The calibration proposal has
43,830 attempts per cell. This is conditional on stable independent within-cell acceptance;
it does not guarantee future calibrated-rule acceptance, runtime or actual experimental coverage.
Parallel scaling is unmeasured. Validation cannot be frozen yet: actual primary and pairwise
threshold files must come from fresh calibration first.

## Reproduction and handoff

Preparation tool: `analysis/tests/prepare_next_stage.py`. Run with numerical threads set to one,
both campaign `.json.gz` archives, both normalized-track archives, this output directory and
`--calibration-manifest` pointing at the proposal. It reads saved evidence, never calls a flight
runner, and rejects holdouts/replays, overlapping attempts, mismatched policies/settings and
stale proposal freezes. Source/archive hashes are preserved in its outputs.

Verification: 27 focused offline checks passed, including protocol feasibility, preservation
of estimated positions, rejection of holdouts/overlaps and conservative attempt planning.
The previous Python CI fixture fix passed GitHub Actions before this preparation.

Next use saved processing diagnostics and independent trajectory/attitude fixtures; additional
flights require a new bounded compute budget. Observed-trajectory integration has controlled
checks; a bounded real-route campaign and review/refreeze of the final domain remain pending.
Fresh calibration, threshold freezing and independent
validation follow only after separate compute authorization. Real IMU bench qualification and
production promotion remain pending hardware/evidence.

# Next-stage research preparation — 2026-10-06

Both 1,000-attempt pilots are complete. The original preparation used their saved records and
seven observed position tracks without new fits. Subsequent 300-case geometry and 72-case
protocol diagnostics are also complete; neither established a protocol that passes all
required comparisons across both crab models. No fresh calibration or validation has run.
Real IMU testing is pending hardware. The current scientific gate is retained; no production
policy or external-GPS fallback is promoted.

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

Actual observed-trajectory replay still needs implementation and checking before execution.
Mount turns, airframe heading, wind, sensor noise and bias would be simulated assumptions,
not recovered measurements. No GNSS accuracy is fabricated and no gaps are interpolated.

## Frozen proposal and compute budget

`calibration-proposed-manifest.json` preserves the earlier source, configuration, eligibility and
one-thread numerical environment. It is now **stale**. `readiness.json` records current stage
status and artifact hashes. Current source is
`27e73b122c3a073357d4a03112da11779969a710bb3a6cc3eb06c333da52ad51`;
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
flights require a new bounded compute budget. Observed-trajectory integration remains pending,
then review/refreeze of the final domain. Fresh calibration, threshold freezing and independent
validation follow only after separate compute authorization. Real IMU bench qualification and
production promotion remain pending hardware/evidence.

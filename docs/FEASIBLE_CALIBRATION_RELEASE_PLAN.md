# Fresh prediction calibration after optimizer qualification

**This plan defines a new finite release; it does not start one.** The
[combined optimizer audit](timing-matrix-combined/README.md) qualifies all 48
computational cases, 24 starting-point pairs and four original-input replays.
All previous calibration campaigns and their unused allowances remain closed.

## Question and fixed method

Can the corrected method produce a finite prediction-error threshold on new
generated examples, then meet the fixed coverage target on a separate cohort?
These are two-minute simulated measurements with declared noise and calibration
settings. They do not establish the error law or confidence level of aircraft
observations.

Retain compensated integration, local timing checks, feasible-anchor bounded
linear solves, the nonworsening guard, all original physical bounds, all 26 or
27 nuisance columns and the existing numerical and forecast screens. Keep both
input formats, three generating candidates, two processing settings and two
prescribed starts: 24 fits per independent noise family. The limits remain
200 evaluations and 620 linear operations per fit, with no retries.

Choose between starts by training cost alone. Save forecasts before scoring
later truth. Every required setting must produce a usable result; missing
settings cannot be silently dropped. Preserve family-level scoring and the
existing cooperative failure rules.

## Proposed cohorts and compute allowance

| Phase | Independent families | Maximum fits | Estimated runtime | Cooperative ceiling |
|---|---:|---:|---:|---:|
| Calibration | 299 | 7,176 | About 139 hours | 240 hours |
| Independent validation | 181 | 4,344 | About 84 hours | 144 hours |

Use four workers with one numerical thread each. The estimates scale the
51.0-minute matrix and 4.6-minute completion controls, together covering 48
completed cases. They include interruption overhead and remain approximate;
different noise draws can need more evaluations. Total expected runtime is
about nine days, with a sixteen-day combined ceiling. Early stopping may end a
failed phase much sooner, without supplying a usable threshold.

Proposed calibration seeds: **281474977410656–281474977410954**.
Proposed validation seeds: **281474977510656–281474977510836**.
Exclude all earlier declared calibration and validation cohorts, including
unexecuted reserved families, plus exposed development controls. Verify the
complete exclusion list and phase separation before freezing. Validation
outcomes remain unavailable during method development.

Maximum native prepayments are **430,229,904 calls and 2,701,855,515,528 packet
visits** for calibration; **260,440,176 calls and 1,635,571,399,032 visits** for
validation. Derive those totals from the unchanged 24-case table and verify them
in software tests. Charge before execution. Preserve interrupted charges and
failures; close unused allowance when a phase ends. Freeze both phase policies,
sources and environment before calibration starts.

This is a proposed new allowance, separate from every closed release. Prepare
and qualify the implementation and exact execution freeze before the compute
review. Do not launch either phase merely because the preceding controls pass.

## Temporary and retained storage

Require at least **55 GiB free before calibration** and **35 GiB before
validation**, checked before any worker or fit charge. The latest closed
calibration supplies 348 retained case examples: their average uncompressed
size is about 1.83 MB and their largest is about 3.01 MB. Scaling those sizes
suggests roughly **12–20 GiB** for calibration case artifacts and **7–12 GiB**
for validation. Publication can temporarily duplicate these files.

The same closed study retains 260.06 MiB of unique compressed payload for its
348 returned cases. Scaling that measurement suggests about **5.2 GiB** for
calibration and **3.2 GiB** for validation, plus metadata, journals and archive
overhead. Those are planning estimates, not upper bounds. Original datasets and
already retained project evidence are additional storage.

After each phase closes, verify and archive it, then compact recoverable working
copies before starting the next phase. Serialize archive writers. Keep original
measurements, source snapshots, failed outcomes and journals; do not delete
unarchived scientific evidence to meet a disk limit.

## Qualification and shared implementation

Reuse the existing campaign executor, family scoring, independent reporter,
calibration handoff and counted solver scope. Add a small release policy rather
than copying a worker or altering the qualified numerical code.

The completed four-case publication supplies the source/environment baseline
already supported by the shared preparer. The separately hash-bound combined
audit supplies proof of complete 48-case coverage. Both refer to the same 241
common execution sources. Bind the exact combined report hash, both constituent
completion hashes, the completed source map and the numerical environment.
Reject any changed shared source or incomplete coverage before preparation or
execution. No preparer hook or numerical-method change is needed.

Require source-bound tests for all cohort exclusions, exact task/prepayment
counts, unchanged physical/noise inputs, complete combined-gate binding, provider
forwarding, work retained after failures, handoff rejection and disk preflight.
Calibration and validation must use the same population/source/environment
identity. Freeze only after these tests pass.

## Statistical gates and interpretation

- Calibration takes the maximum of 299 complete independent family scores to
  target 99% coverage with 95% confidence on the declared generated population.
- Independent validation targets 95% family coverage with 95% confidence,
  allowing at most four failed families among 181 under the existing exact rule.
- Stop calibration cooperatively if both starts fail a required setting. Stop
  validation at its fifth failed family. Retain every returned outcome.
- Validation requires a finite, audited handoff from the entire new calibration
  cohort. Partial cohorts and changed methods or environments cannot supply it.

Publish every planned row and returned result without refitting during audit.
Verify hashes and archived replay, then update the public roadmap. These targets
calibrate generated prediction errors; they do not establish significance of
the two-stage Earth-model comparison on actual observations. The original
53 aircraft results and protected ESA confirmation groups remain unchanged.

[Next analyses](NEXT_STEPS.md) · [Optimizer qualification](timing-matrix-combined/README.md) ·
[Previous closed calibration](prediction-calibration-timing/INTERPRETATION.md).

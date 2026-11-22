# Full-size observed-input preflight

## Question

Can the fixed two-law prediction machinery construct its error operators on
the already designated ESA development interval at the recording's real size,
within a finite runtime and memory allowance? This checks software feasibility
and the earlier/later boundary. It does not fit or compare Earth models and
does not score withheld receiver positions.

## Frozen input and scope

Use only the hash-verified prepared recording 187 from the completed ESA
development preparation. It has 360,028 IMU packets and 1,200 receiver epochs.
The first 800 receiver rows are available for initialization; the final 400
remain unopened. The training IMU prefix is 239,867 packets under the existing
0.01-second time-offset bound. The original files and seven reserved ESA
confirmation groups are outside this preflight.

Use the two exact supplied IMU error laws from the generated whole-period
study, labeled `increment` and `point`. Their numerical levels are synthetic
stress assumptions, not measured hardware limits. Hold the candidate at the
specified-field globe, no upstream removal, the earlier-only reported-short
receiver policy, and the existing height-gravity anchor. These settings are
technical inputs, not a model outcome.

## Four bounded tasks

Construct one full-size covariance operator for each pair of supplied law and
prediction target: physical position and future receiver report. The physical
target is not scored because the true aircraft path is unobserved. Each task
records the exact input/source/environment hashes, time grid, state dimension,
operator configuration, peak resident memory, elapsed time, and charged native
calls. It must confirm the same 800-epoch training prefix and must never read
later receiver values.

Each task may charge at most 601,895 native calls and the same number of packet
steps: a training operator over 239,867 packets and 800 queries, then a full
operator over 360,028 packets and 1,200 queries. Each packet needs one full
evaluation and each query at most one partial evaluation. The four tasks
together may charge at most 2,407,580 native calls. Use four workers of one
numerical thread each, a four-hour cooperative
wall ceiling, at least 35 GiB free disk at launch, and no automatic
scientific retry. These are ceilings, not expected work. An interruption must
preserve charged starts and use separately qualified task-level recovery.

## Release gates

Before launch, qualify the observed adapter on a short native known-answer
control, verify the existing ESA input and split hashes, freeze the complete
source and numerical environment, and prove task-level interruption recovery
in a finite test. A source-bound worker preflight must pass before the four
full-size tasks start. Any failed task blocks the dependent observed pilot;
its evidence stays saved. A passing preflight only permits a separately frozen,
finite observed development study. It does not establish error-law adequacy,
coverage, calibration or a scientific decision.

The no-fit operator constructor now passes a short native control for both
targets plus a precharge rejection check. The observed material and two-law
forecast adapters pass four additional focused checks. These software tests
do not replace the source-bound full-size worker and recovery qualifications.

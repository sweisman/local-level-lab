# Earlier-only forecast-error transfer: development plan

## Question

Can error measured on a prediction made **within the earlier part** of an
aircraft recording describe error in a later, equally long prediction? This
checks a possible way to estimate forecast uncertainty without using the
period being judged. It is a development test, not a confidence interval or
an Earth-model comparison.

## Fixed data and calculation

Use only the three preselected NASA development recordings in the sealed
retrospective pilot. Read its hash-checked prepared IMU and receiver inputs;
do not reopen originals or use the seven reserved ESA groups. Keep all recorded
IMU increments and the three receiver-coordinate axes.

For a recording with `N` receiver epochs, set `A = floor(N/3)` and
`B = floor(2N/3)`. Fit once using only receiver epochs before `A` and predict
the next `H = min(B-A, N-B)` epochs. In a **separate fit with the same source
version**, use only epochs before `B` and predict the final `H` epochs. The
first prediction supplies an earlier-only error pattern; the second is its
withheld transfer check. Each forecast must be saved before its scoring
positions are opened. Neither fit receives receiver positions after its cut.
Store IMU increments and times once per recording; keep each cut's training
receiver positions and its scoring positions in separate hashed inputs. This
avoids duplicating the large packet stream.

Use the specified-field globe candidate solely as a conditional error-law
diagnostic. Include both declared upstream-processing cases, both existing
clock conventions and both fixed optimizer starts. This makes
`3 recordings × 2 processing cases × 2 clocks × 2 starts × 2 cuts = 48 fits`.
Keep the original calibration bounds, position weighting, 200-evaluation
ceiling per start and continuous propagation without receiver resets. Select
the primary start at each cut by **its own earlier training cost only**.
Report every failed or bound-active fit; do not substitute a successful start
from the other cut.

For each qualified matched setting, report signed errors, north/east/up RMS
in four consecutive equal-count forecast quarters, maxima, endpoint error,
and the later-to-earlier ratio at the same horizon. Show the full distribution
across recordings rather than count the repeated settings as independent
flights. No ratio or threshold is chosen from the later scores. If any fit is
unqualified, that setting abstains. A successful transfer on three development
recordings still cannot establish a population coverage rate.

## Release gates and finite resources

The historical pilot's source differs from the current checkout in 15 of 90
declared files. Therefore do **not** compare a new inner fit with the old
outer fit as if they used the same implementation. Preserve the old result;
qualify the current-source training/forecast path on generated known-answer
cases at both cuts before observed starts. The new study must freeze its exact
source, numerical environment, prepared-input hashes, cut epochs, scoring
separation, task IDs and qualification report. New code belongs in a small
`lll.studies` adapter using the shared training and forecast library, not a
copy of the old worker tree.

Allow at most 48 starts, 200 charged training native evaluations plus one
charged forecast per start, four workers with one numerical thread each, and a cooperative
six-hour wall ceiling. The exact packet-visit allowance is calculated from
the sealed input lengths before preparation. Prove task-level interruption
recovery in a finite test. Completed failures remain sealed; unfinished work
can resume only with unchanged inputs, method and environment under the
remaining allowance. Never expand this study's budget or refit a completed
task. Preserve all scores and failures; publication reads saved results only.

The technical gate is complete, hash-verified results and exact accounting.
The scientific output is a description of transfer or failure, with
`scientific_decision = abstain`. Any later uncertainty rule or confirmation
campaign needs a separate freeze and an independently justified coverage gate.

Before the source-bound qualification, run a **99-second generated motion
control** with 200 Hz increments and one receiver position per second, using
the existing independent analytic trajectory. Check both cuts under the
header-elapsed clock and the no-removal processing case. Require numerical
convergence at both cuts and the original pilot's fixed physical screen:
later horizontal RMS at most 10 m, height RMS at most 30 m, maximum horizontal
error at most 50 m and maximum absolute height error at most 150 m. This is
a necessary method check, not evidence of aircraft uncertainty coverage.

[Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md) ·
[Original retrospective pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)

## Preparation status

The shared prediction input helper now accepts an explicit earlier cut while
keeping its original two-thirds default. A separate splitter builds both
training inputs, shares the IMU stream once, and keeps scoring positions
outside both fit inputs. Eighteen
focused prediction/split/growth checks pass. Longer generated physical-accuracy
qualification, bound recovery proof and the frozen 48-fit study have not run.

The actual native fit/forecast path has now completed eight short generated
technical cases covering both cuts, both clock conventions and both processing
assumptions. These checks verify execution and scoring separation; they do not
set a physical accuracy or coverage bound. The source-bound qualification
report and specific reboot-recovery check still precede observed starts.
The two predeclared 99-second generated cases also pass numerical convergence
and all four physical accuracy limits. No aircraft observation entered these
controls. The combined source/environment-bound qualification remains next.

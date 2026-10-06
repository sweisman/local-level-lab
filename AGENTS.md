# Codex preferences for Scott Weisman

## Who you're working with

The user is **Scott Weisman** — not Stephen, not Steven. GitHub `sweisman`,
email sweisman@gmail.com (a handle; do not infer a first name from it).
Always use "Scott" in copyrights, licenses, attribution lines, signed
correspondence, and anything else user-facing.

## Token economy

Scott works against tight token / plan-session budgets. Wasted tokens cost real work.

- Verify the cheapest sufficient way; don't run a heavy variant when a lightweight check proves the point.
- Don't re-read a file just edited; trust successful edits.
- Keep replies tight and lead with the result.
- Before expensive actions (large builds/renders, full re-derivations, multi-agent fan-out), name the cost and ask.
- One careful pass beats iterative polishing that wasn't requested.

## Workspace privacy

Leave unfamiliar paths outside the documented project corpus alone entirely.
Use README tables, manifests, and project instructions to identify that corpus.
Do not scan or enumerate unfamiliar paths, add them to git or `.gitignore`,
document them, flag them as anomalies, or ask what to do with them.
If a directory listing happens to surface them, do not comment.

## Git operations

Do not initiate any git operations without explicit consent. This includes
adding, committing, pushing, stashing, resetting, checking out, restoring,
rebasing, tagging, creating/deleting branches, and creating PRs or issues.
If a git operation is the next step, ask first (for example, "Want me to commit and push?").
Finishing a feature is not permission to commit it.
When Scott explicitly requests an operation, proceed without another confirmation
for that operation only.

## Commit granularity

Bundle related work into one commit per logical unit, across files and sessions.
Use the final coherent state and one message describing the whole.
Only split commits when Scott requests granular commits.
If many commits were made without being asked, surface what's pending and ask
how to consolidate instead of pushing them separately.

## Shell commands

Run each step as its own shell invocation. Avoid compound expressions, chains,
pipes for trimming output, and heredoc appends when a simple command suffices.
Use tool output limits or scripts that print less.

## Development environments

- Always use `~/venv/bin/python` and its pip for Python work and tests; do not use system Python or create another environment.
- Always use the installed JDK under `~/.local` for Java/Gradle work (currently `~/.local/jdk21`), with `JAVA_HOME` set accordingly; do not use the system JDK or download another.

## Analysis campaign handoff — 2026-10-05

### Latest authorization and handoff — 2026-10-06

Scott authorized the eight-case watchdog diagnostic and then **another exactly 1,000 development
flight attempts** (~3.3 hours), choosing that budget explicitly. The new documented corpus is
`docs/development-1000-20261006/`. Fresh seeds are 600300–600466, disjoint from the original pilot;
paired across the same three truths × `bias_mixed`/`wind`, 166/167 attempts per cell. Geometry,
sensor variant and nuisance fits match the original campaign; the candidate now preregisters
`rank_min_relative_margin=0.1`. All ranks are recorded. This does not authorize calibration,
validation, production promotion, another thousand flights, or git operations. Do not ask again
to resume these same missing attempts after a chat/network/token interruption.

Initial launch verified: actual outside-sandbox PID **3515674**, manifest hash
`bebc8dee5a6c6d291015fa3973b0759d05f408efdc8404335e89dac35d47fb0f`, scientific source hash
`3f720b4148e0b0bd8989eaa7e72600997b64f3a88664dc3cd5d21155d3a4be8d`.
Five attempts were checkpointed with zero failures at the initial survival check. The source
and environment match the frozen proposal. Read current status rather than treating this
initial count/PID as current. Outside-sandbox processes are not visible to `os.kill(pid, 0)`
inside the sandbox; use an outside-sandbox `ps` check if status is stale before considering resume.
Verification before launch: 83 focused checks passed; no additional flight synthesis used by tests.

The eight diagnostic replays finished in 52.05 seconds. Complete saved inputs/results and a
known-wind oracle review are in the original campaign directory:
`watchdog-diagnostic-20261006.json`, `watchdog-review-20261006.json`.
Wind seed 600107 with zero mount creep lost segments 0/6 and nine bins; design retention fell
from 0.394 to 0.196. Known-wind heading correction removed false flags and retained all four
true-slip controls. It is a diagnostic using simulator information, not an operational correction.
`magnetic-watchdog-2` reports apparent yaw change and unresolved crab/slip ambiguity, retaining
conservative exclusions. Research now saves full watchdog output and pre-exclusion geometry.
No data-dependent threshold relaxation or production promotion occurred.

The worker now automatically writes wide/narrow rank sweeps, `magnetic-summary.json` and lossless
`campaign.json.gz`/`records.jsonl.gz` archives. The new corpus also contains the original frozen
manifest, append-only fsynced records, atomic status and local launch/log/lock; `recovery.jsonl`
exists only if repairing a partial final write. Existing success/failure attempts are never rerun
to improve acceptance. Only completed attempts count towards the exact 1,000 budget.

Read `docs/development-1000-20261006/status.json` first. If active, do not start another worker
or alter scientific source/environment. If interrupted with unchanged source/environment,
resume using this exact command (omit `--resume` only for the first launch):

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/development_campaign.py --output docs/development-1000-20261006 --flights 1000 --seed 600300 --rank-min-relative-margin 0.1 --resume --detach
```

Use `exec_command` with `sandbox_permissions="require_escalated"` so the already authorized
detached worker survives command/chat disconnection. Check status and actual PID in launch.json;
the worker holds a process lock, verifies source/environment before and after each fit, and
rejects mixed or malformed checkpoints. No network or model calls are needed while it runs.

On completion, report by truth/scenario/rank: failures, exclusions, bootstrap convergence,
conditional null rejection, primary separation, pairwise decisions/abstentions, rank stability,
magnetic rates/selection and runtime. Refresh README/VALIDATION and the handoff with measured
results. The shared seeds are paired; these are not 1,000 independent draws of one null.

`docs/flight-calibration-proposed-manifest-20261006.json` is a frozen **proposal**, not an approved
launch or final policy. It uses rank 2 and the 10% stability margin; planner acceptance now
applies that proposed margin to saved pilot records. Historical estimate: 514,092 combined
attempts / ~70 serial days, or 576,000 / ~78 days with the draft 45,000-calibration and
51,000-validation attempt reserves per cell. Review/refreeze it after the new pilot; a source
change invalidates it. Actual primary and separate pairwise calibration files must precede
a frozen independent-validation manifest. Do not relabel development seeds or relax sample goals.
The broader geometry/nuisance and pooled-summary domains remain separate work.

Scott authorized one bundled commit and push of the stable follow-up code, documentation,
completed diagnostic/track artifacts and the new pilot's frozen manifest. Actively changing
campaign status, checkpoints, logs and generated results are excluded until the worker finishes.
The published manifest alone is not a resumable checkpoint: if a fresh clone lacks status or
records, recover the original journal before resuming, never rerun completed attempts.
Further git operations require fresh consent after this authorized commit/push.

Stable work was committed and pushed as **`8f2b423`**. Only the active campaign's frozen manifest
was included; changing worker outputs remain local. Scott subsequently authorized committing
and pushing the documentation refresh and Python CI fixture fix together, excluding campaign
outputs. Further git operations require fresh consent after that operation.
CI run `37431079994` reported 271 passing tests and one failure: the campaign-cost fixture
omitted convergence evidence now required by the shared gate. The fixture is corrected; the
scientific gate is unchanged, with a regression check that missing/failed convergence is excluded.
Both changed test files are outside the active campaign's explicit implementation-hash list.
Verification: the repaired cost test and four development-review tests passed (5 total, 1.15s).
The scientific implementation hash remains unchanged. The documentation refresh covers protocol,
in-app guidance, privacy/browser behavior, format metadata/events, third-party licensing,
primary-corpus/validation boundaries, methodology, README and contribution guidance.

### Real position tracks supplied during the active pilot

Scott explicitly supplied these three files in `/home/sweisman/` for development geometry:
`2025-09-01 etihad 10 ord auh.csv`, `2025-08-19 etihad 9 auh ord.csv`,
`2025-08-19 aa 1433 ord lax.csv`. Do not scan home or inspect other files. These exports have
positions, displayed times, ground course, speed and altitude; no IMU. Source labels say FlightAware
ADS-B. Scott says position increments are 20–60 seconds and any additional downloads will be few.

Documented derived corpus: `docs/flight-geometry-20261006/README.md`, `summary.json`,
`normalized-tracks.json.gz`. Importer `analysis/tests/import_flight_tracks.py` preserves missing
measurements and hashes the originals; three cheap parser/coverage tests passed. Tracks contain
1,234 / 1,330 / 449 points over 12h54m / 13h47m / 3h38m. Etihad tracks reach 49.11°N and
56.50°N; ORD–LAX spans 33.94–41.97°N. Maximum gaps are 184 / 158 / 45 seconds. There are
68 / 76 / 29 overlapping 75-minute windows with >=95% position coverage (excluding intervals
over 90 seconds); these are not independent samples or accepted scientific flights.

Displayed timezone and altitude reference are unconfirmed. Do not infer absolute UTC timestamps
or treat reported altitude as known geometric height. No missing values have been filled and no
new simulations launched. The new standalone importer is outside the active scientific hash;
existing frozen source was not changed. Develop trajectory replay only after the current pilot
finishes, under a separately scoped compute budget, with simulated sensor/nuisance assumptions
explicit. If a few additional routes are offered, prioritize high-latitude (>60°), equatorial,
and predominantly north–south geometry; the current three are enough for initial integration.

### Collection identity and GPS recovery — 2026-10-06

Scott requested comprehensive constrained airline selection and airline/flight/date metadata
for verifying flights, cross-checking phone GPS and recovering geometry if GPS is unavailable.
New flight setup uses the offline OpenFlights directory (`android/app/src/main/assets/airlines.json`),
6,136 named coded carriers at source revision `5d623a6969a1adee7961cf1c9a8a212c4a784713`.
Directory source/provenance/license are documented alongside it; ODbL applies separately from
recording CC0 and source AGPL. It includes historical entries, and upstream activity is unreliable;
do not present membership as proof a flight or airline currently operates. No arbitrary airline
entry is allowed. Update the source snapshot when a carrier is missing.

`FlightIdentity.kt` validates the chosen operating carrier, matching flight-number prefix,
calendar date and different three-letter airport codes. New manifests include carrier IDs/codes,
directory revision, origin-local departure-date basis and `track_verification="pending"`.
`AirlinePicker.kt` searches names/aliases/codes/countries and keeps shared codes distinct.
The flight-history browser action supports checking the actual date/route; opening a link does
not mark verification successful. No automated provider verification or scientific fallback
has been implemented. Both require a dated actual track, temporal overlap, observed coverage,
checked clock alignment, provenance and an external-position/timing uncertainty model.

Missing-GPS recording remains explicitly acknowledged and continues IMU capture and attempts
to obtain GNSS. `RecorderService` logs phone-clock anchors and GNSS availability at flight
start/resume. These are uncertified wall-clock readings, not GNSS timing. Keep raw recordings
and provider track artifacts separate; never fabricate GNSS accuracy or satellite counts,
fill estimated positions as observations, align by gyro agreement, or relax the scientific gate.
Collection/docs changes do not modify the active pilot's frozen scientific implementation.
Focused Android verification passed: `FlightIdentityTest` (three tests), with the installed
JDK 21 and offline Gradle cache. The full app Kotlin source compiled as part of that check.
Scientific hash was rechecked unchanged at
`3f720b4148e0b0bd8989eaa7e72600997b64f3a88664dc3cd5d21155d3a4be8d`.
These collection changes are included in Scott's authorized bundled commit/push of stable files.
Further git operations require fresh consent after that operation.

### Direct public scraping — 2026-10-06

Scott then authorized direct scraping and requested Europe/Middle East–South Africa cases.
Four complete public FlightAware coordinate tables were retrieved for 2026-10-02 departures:
FI680 SEA–KEF (560 points), SQ938 SIN–DPS (270), LH572 FRA–JNB (602), EK761 DXB–JNB (518).
Documented corpus: `docs/scraped-flight-geometry-20261006/README.md`, four CSVs following his
filename convention, corresponding `.provenance.json` files, `summary.json`, and
`normalized-tracks.json.gz`. Provenance includes exact public source URLs, HTML/export hashes,
retrieval time, page timezone and UTC observation bounds. No login/session was needed.

Extractor: `analysis/tests/extract_flightaware_track.py`. Use actual FlightAware history links;
guessed times from another tracking site's schedule can return an empty coordinate table.
Pages label their clock EDT, not UTC; exports convert the dated New York clock to UTC, including
weekday crossings. Desktop full-precision values are retained, rounded mobile duplicates and
non-coordinate event rows are excluded. Raw downloaded HTML remains in `/tmp`; factual CSVs and
provenance are durable. Seven focused extraction/import tests passed.

Provider-estimated/approximate points number 70 / 5 / 262 / 174. Keep them explicitly labeled;
they are not observed receiver fixes. Normalized format `position-track-2` now preserves the
source label and estimate flag per point, and excludes estimated endpoints from observed-window
coverage. The original supplied tracks were renormalized too: 131 / 91 / 0 provider estimates;
corrected >=95%-coverage window counts are **67 / 74 / 29**, replacing the historical 68 / 76 / 29
counts above. Source CSVs were not changed. Original supplied timezones remain unconfirmed.

New scraped tracks have maximum gaps 430 / 148 / 148 / 174 seconds and 10 / 0 / 12 / 0 overlapping
75-minute windows at >=95% reported coverage under the provisional 90-second gap limit. FI680
reported positions reach 67.97°N. African tracks have substantial estimated stretches. Do not
treat an entire public table as continuously observed motion, fill missing sensor data, or
claim scientific eligibility from these geometry summaries. No additional scientific fits ran
and existing active-campaign source was untouched. Further scraping within Scott's requested
geometry-development scope is authorized; full simulation/campaign compute and git operations
still follow the existing budget/consent rules.

**Completed 2026-10-06:** all 1,000 authorized attempts finished in 3h16m (11.73 seconds
per attempt). No worker needs resuming. `status.json` is `complete`; `campaign.json` and
`rank-sweep.json` are saved. There were zero analysis failures, 906 eligible flights, and
valid bootstrap convergence in all 1,000 fits. One eligible `sphere_rotating/bias_mixed`
flight rejected its generating model under the uncalibrated diagnostic rule (1/166 in that
cell). This is development evidence, not a validated false-rejection rate.

Ranks: 927 rank-2, 73 rank-1; 877 rank-2 flights were eligible. The wide default cutoff sweep
changed rank in 916 flights; `rank-sweep-narrow.json` uses ±10% and changes rank in 47 flights,
also the 47 within 10% of the current boundary. Gate exclusions overlap: 91 design-contrast
failures, 16 WMM-slip sensitivity exclusions and one prior-dominated fit, affecting 94 flights.
880 uncalibrated pairwise three-model winners matched the generating model; 120 abstained.

Acceptance / eligible rank-2 counts per cell:

| Truth / scenario | Attempts | Eligible | Eligible rank 2 |
|---|---:|---:|---:|
| rotating globe / mixed bias | 167 | 166 | 166 |
| rotating globe / wind | 167 | 137 | 137 |
| still globe / mixed bias | 167 | 166 | 166 |
| still globe / wind | 167 | 138 | 135 |
| flat disc / mixed bias | 166 | 164 | 151 |
| flat disc / wind | 166 | 135 | 122 |

The next work is development review of wind-related geometry exclusions and rank stability,
then a new frozen calibration plan/budget. At worst observed rank-2 acceptance 122/166,
the current sample goals imply about 39,847 calibration + 45,132 validation attempts per
cell: **509,874 attempts / 69 serial days**, assuming that acceptance persists under the
calibrated rule. This is a point estimate, not a guaranteed budget. The old 35,000/40,000
attempt reserves are insufficient at that acceptance; do not launch the old proposed manifest.
No thresholds were estimated and no independent validation ran. README and VALIDATION
have been updated with the completed results. Git operations still require Scott's consent.

**Follow-up 2026-10-06:** completed development work was committed and pushed as `dd8575f`.
The subsequent saved-record selection review is a separate, uncommitted draft:
`analysis/tests/review_development.py`, its tests and
`docs/development-1000-20261005/selection-review-20261006.json`.
It requires the frozen shared gate source and performs no fits or threshold estimation.
All 91 design failures have a magnetic slip flag (88 wind, 3 mixed bias). The watchdog flags
132/500 wind and 6/500 mixed-bias flights despite zero injected mount creep. The recorded
data establish an association; they do not expose the discarded segment details needed to
prove the cause. Review of `slip.watchdog` shows it uses GNSS course and WMM declination
without a crab term, so wind-induced aircraft-heading changes are a specific hypothesis to test.
Do not disable the slip gate or loosen it merely to raise acceptance.

Hypothetical minimum relative rank margins 0%, 5%, 10%, 20% retain 906, 897, 894, 866
flights, respectively; all retain the one diagnostic null rejection. A 10% margin retains
870 eligible rank-2 flights and gives a worst-cell rank-2 acceptance of 121/166: approximately
514,092 full-campaign attempts / 69.8 serial days under the same planning assumptions.
No proposed margin has been adopted or frozen for calibration. The next useful bounded
diagnostic is the magnetic watchdog under wind versus true injected mount slip, retaining
per-segment rates and before/after-exclusion geometry. Obtain a new compute budget before
additional flight analyses or a fresh campaign; the 1,000-flight authorization is exhausted.
A concrete eight-case proposal is `docs/development-1000-20261005/watchdog-diagnostic-plan-20261006.json`:
rotating-globe seeds 600100 (passing wind geometry) and 600107 (failing wind geometry),
mixed-bias/wind cases, each with recorded zero creep and a 3°/h yaw-creep positive control.
Geometry-only replay, zero bootstrap, 120-second total cap; retain per-segment watchdog and
post-exclusion geometry. No proposed case has run. These replays must never count as new
independent calibration/validation evidence.

Scott authorized **exactly 1,000 development flight attempts**, about 3–3.5 hours at the
measured runtime. He declined the full 48–58 serial-day calibration/validation campaign.
This authorization includes launching the local worker and resuming its missing attempts;
it does not authorize additional flights, full calibration, production promotion, or git operations.
Do not request the same campaign authorization again after a chat/token/network interruption.

The review fixes #1–#7 and optional partial pairwise evidence/pooling are implemented.
Earlier commits are `f687734` (review implementation) and `0be7ad0` (cruise qualification
and explicit protocol). Scott requested commit and push of the completed development work
on 2026-10-06: batching, numerical-thread freezing, calibration-margin/power planning,
nuisance subsets, the resumable worker, campaign evidence and documentation belong in one
coherent commit. Further git operations require new consent.

The documented campaign corpus is `docs/development-1000-20261005/`:

- `manifest.json`: original source/configuration/policy/environment freeze.
- `records.jsonl`: append-only completed attempts, including analysis failures; each is fsynced.
- `status.json`: atomic progress, PID, counts, state and error.
- `launch.json`, `worker.log`, `run.lock`: launch details, durable worker output and exclusion of duplicate workers.
- `campaign.json`, `rank-sweep.json`: automatically generated final results and cutoff sensitivity.
- `campaign.json.gz`, `records.jsonl.gz`: lossless published archives of the complete campaign
  and checkpoints. Unpacked large files and local worker bookkeeping are generated artifacts.
- `rank-sweep-narrow.json`: post-run development diagnostic using ±10% cutoffs, with no refits.
- `selection-review-20261006.json`: recorded gate-margin sensitivity, watchdog association
  and provisional costs, with source hashes; no new flight or calibrated decision.
- `watchdog-diagnostic-plan-20261006.json`: unrun, eight-case diagnostic proposal with a
  120-second cap; needs a separately authorized compute budget.
- `recovery.jsonl`: preserved bytes if resume repairs an incomplete final write; exists only when needed.

On a fresh clone, extract either archive only if its unpacked counterpart is needed. Example
for reading the published results without creating another file:

```sh
/home/sweisman/venv/bin/python -c 'import gzip,json; d=json.load(gzip.open("docs/development-1000-20261005/campaign.json.gz", "rt")); print("Completed:", len(d["records"]))'
```

Do not resume this completed campaign to reanalyze its results. If restoring a genuinely
interrupted run on another host, restore its entire original checkpoint journal before
using `--resume`; a missing unpacked journal must not be treated as zero completed attempts.

Worker: `analysis/tests/development_campaign.py`. It uses fresh development seeds
600100–600266, interleaved across three truths × `bias_mixed`/`wind` (166 or 167 attempts per
cell). Shared seeds make paired comparisons; the 1,000 flights are not 1,000 independent
draws of one null distribution. Geometry is exactly `docs/development-protocol-75min.json`.
Settings: SPP, dynamic crab, dynamic sensor bias, axis/segment weights, measured forward-axis
uncertainty, moving blocks of length 15, 20 complete nonlinear bootstrap replicates, pairwise
evidence. All observed ranks are retained for development diagnostics. Numerical thread
settings `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS` are all **1**.

Fresh-chat procedure:

1. Read this handoff and `status.json`; inspect `worker.log` only if necessary. An active worker
   needs no further model calls or network. Do not start a duplicate or change scientific source
   while it runs; source/environment changes stop the worker and prevent mixing evidence.
2. If interrupted and the original source/environment remain unchanged, resume the same
   campaign with the command below. Completed successes **and failures** are skipped, never
   rerun to improve acceptance. A process lock prevents duplicate workers. Resume preserves
   a truncated final write before repair; malformed complete records are rejected.
3. When complete, use `campaign.json` and `rank-sweep.json` to report failures, exclusions,
   rank frequencies/stability, bootstrap convergence, conditional false rejection, model
   separation, pairwise decisions/abstentions and runtime separately by truth/scenario/rank.
   Update README/VALIDATION and this handoff with the measured results before any authorized commit.
4. Recompute the remaining campaign cost from these records. Development is not fresh
   calibration or independent validation: about 166 accepted samples per cell cannot establish
   the planned 0.0027 false-rejection bound. Do not manufacture thresholds by weakening the
   frozen sample-size criteria or relabeling development seeds as calibration/validation.

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/development_campaign.py --resume --detach
```

For Codex execution, a detached child launched inside the per-command sandbox is killed
when that sandbox exits. Launch/resume this command using `exec_command` with
`sandbox_permissions="require_escalated"`, explaining that this is required for the already
authorized background worker to survive command/chat disconnection. The corrected launch
on 2026-10-05 was outside the sandbox; its actual PID and command are in `launch.json` and
`status.json`. The first sandbox launch ran no flights. Check progress before attempting any
resume; do not use the historical failed launch PID.

Remaining research order: use development results to decide geometry/candidate/rank envelope
and any stability gate; freeze final source/config/policy/environment; obtain a new compute
budget; run fresh calibration (primary and separate pairwise thresholds); freeze independent
validation with those actual decision files; run and assess simultaneous exact bounds.
The proposed restricted plan is `docs/flight-calibration-proposed-manifest-20261005.json`:
29,285 accepted calibration and 33,169 accepted validation samples per truth/scenario cell,
calibration alpha 0.00135, claimed alpha 0.0027, 18-test family, validation failure budget 64.
Its cost is provisional, and it must be refreshed after source/config/environment changes.
Its old attempt reserves also need revision based on the completed development acceptance above.
Broader geometry/nuisance domains, other sensor variants and summary-level pooled pairwise
calibration/validation remain separate work. Production promotion requires a reviewed policy revision.

Earlier evidence: `docs/bootstrap-development-20261005.json` and its compressed raw artifact
record 18/18 accepted complete-bootstrap pilots at rank 2; another timing run had rank 1.
No fresh empirical threshold or independent 3σ validation claim has been established.
Collection work is outside the current analysis campaign scope.

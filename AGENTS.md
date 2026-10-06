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
- Scott has an 11th-generation i7 and authorizes up to two CPU threads/workers for routine
  computation. For new numerical runs, default `OPENBLAS_NUM_THREADS=2`, `OMP_NUM_THREADS=2`
  and `MKL_NUM_THREADS=2`; use at most two workers for builds and other parallel tasks.
  Avoid multiplying worker concurrency by numerical thread counts beyond two total.
  This is a resource preference, not authorization for additional campaign attempts or time.
  Existing frozen campaigns retain their original thread settings on resume. The completed
  `geometry-development-20261006` batch used one numerical thread; switching a future
  campaign to two requires a new environment freeze and refreshed runtime/cost measurement.

## Analysis campaign handoff — 2026-10-05

### Current state and documentation — 2026-10-06

**All campaigns are complete; no worker is active and no additional flights are authorized.**
The latest 72-case protocol comparison finished with zero fit failures, all fits converged,
and 516.9065152532421 charged seconds (8m37s). Do not resume completed campaigns or spend
unused time on extra cases. Both 36-case arms fail the all-comparisons requirement.
Original/dynamic: 18/18 design and screen passes, all rank 2. Original/wind: 9/18 design,
6/18 screen passes, 15 rank 2 and 3 rank 1. Revised/dynamic: zero passes, all rank 2;
revised/wind: zero passes, 12 rank 2 and 6 rank 1. All model decisions abstain.
The revised IMU turn at minute 20 overlaps the first simulated aircraft turn; its causal
effect remains unisolated. The simplified ideal-axis fixture did not establish a usable protocol.
`docs/protocol-development-20261006/review.json` verifies the freeze, task identities,
compressed journal and recomputed scores. Current source is
`27e73b122c3a073357d4a03112da11779969a710bb3a6cc3eb06c333da52ad51`,
environment `52cba9baed64e4096cc4b0bba352dbe3a3a366127a70ebcb4aa24fd8a91a8c98`,
manifest `77a9c8e829368a8dcb3d4e202e0cc826c72978ea96267d215b82be911ec71838`.

Next use saved processing diagnostics and independently checked trajectory/attitude fixtures
before choosing another protocol. More flights require a fresh budget. Old calibration
proposals are stale; review/refreeze the final source/configuration/policy/environment,
then fresh primary and pairwise calibration, frozen thresholds, and independent validation.
Real IMU bench qualification and observed-track replay remain pending. Never present
development screens as calibrated decisions or as a demonstrated three-model separation.

Reader-facing documentation must be understandable to literate nonspecialists: explain
**IMU (inertial measurement unit)** on first use, then use IMU throughout; lead with the
expected rotation signal in steady level flight and distinguish it from measurement bias.
Explain what the project does, how it works, measured status, limits and next needs in prose.
No JSON-file links or personal/chat/authorization narratives in the public overview and guides.
Keep technical records separately rather than deleting evidence. New documented files are
`docs/DEVELOPMENT.md`, `docs/METHODOLOGY_TECHNICAL.md`, `docs/VALIDATION_TECHNICAL.md`,
`docs/BENCH_TECHNICAL.md`, `docs/CURATION.md` and `docs/EVIDENCE_TECHNICAL.md`.
The README and public methodology/protocol/bench/curation/validation/evidence guides were
rewritten accordingly. The related implementation, campaign results and documentation form
one coherent publication unit. The user authorized committing and pushing that unit after
the documentation update; subsequent git operations need fresh explicit authorization.
Scientific verification: 57 focused checks passed in 1.65s before documentation-only edits.

### Latest authorization and handoff — 2026-10-06

**Latest audit and protocol follow-up:** Scott authorized the saved-record audit, then explicitly
approved **72 geometry-only evaluations with a 15-minute cumulative cap and two numerical threads**.
New corpus: `docs/protocol-development-20261006/` (see its README for launch/resume and artifacts).
Historical initial launch: outside-sandbox PID **3564298**, four checkpointed evaluations, no failures.
Manifest hash `77a9c8e829368a8dcb3d4e202e0cc826c72978ea96267d215b82be911ec71838`,
two-thread numerical environment hash
`52cba9baed64e4096cc4b0bba352dbe3a3a366127a70ebcb4aa24fd8a91a8c98`.
Those initial counts are superseded by the completed 72-case results above. Do not resume.
Input: `docs/geometry-development-20261006/protocol-comparison-plan.json`. Paired fresh seeds
600501–600503, old exact protocol versus nominal 90-minute opposing/repeated headings, three truths,
two nuisance scenarios, both crab fits, zero bootstrap. Protocols interleave; each arm has 36 cases.
Do not exceed 72 cases or 900 charged seconds, refill budgets, restart old campaigns or ask again
to resume these same missing attempts under an unchanged freeze. Git operations still need consent.

Audit tool/artifact: `analysis/tests/audit_geometry.py`, `docs/geometry-development-20261006/audit.json`.
It uses saved records and analytic bins only, never flights or nonlinear solves. Fixed nuisance-SVD
unit dependence in `inference.py` by unit-column scaling; added pre-cutoff contrast diagnostics and
explicit conditioning on retained bins/forward/mount axes. Wind Jacobians pass anchor finite-difference
checks. Six-heading 60-minute fixtures hit the ten-minute cruise minimum and lose intermediate headings;
the 180-minute analytic fixture loses rank to dynamic bias. All six no-fit records are watchdog/no-bins.
Seven saved evaluations (all six wind controls plus one stress case) flip worst-anchor rank under ±10%
cutoff changes. Keep thresholds and protective gates unchanged; do not overwrite historical results.
The opposing 90-minute candidate passed ideal tangent checks but failed the completed simulator
comparison. It has not been tested with a real IMU.
Verification: 57 focused checks passed in 1.65s. Current scientific source hash is
`27e73b122c3a073357d4a03112da11779969a710bb3a6cc3eb06c333da52ad51`.
Old calibration freezes are stale after source/thread changes; review/refreeze the final domain first.
Completed campaign artifacts preserve both arms and all failures/selection/ranks/contrast retention
by seed/scenario/truth/crab. No calibration or promotion
is authorized. Unused time does not authorize extra cases. Bench IMU and observed-track replay pending.

**Current geometry follow-up:** Scott said "go" after the published next-stage preparation.
**Complete:** `docs/geometry-development-20261006/status.json` reports 300/300 evaluations,
six retained no-fit results, 1,838.56 charged seconds (~31 minutes). Do not resume or use the
unused time for extra cases. Zero of 25 geometries passes all contrasts across both crab models.
The exact control passes all six dynamic-crab cases and no wind-crab cases; still-globe versus
disc is limiting under wind. Dynamic/wind fits have 133/130 rank-zero results. All six no-fit
cases share the -65° / two poor headings / 180-minute / 270 m/s / no-turn / mixed-bias cell.
`review.json` verifies freeze, case identities, archive equality and recomputed scores.
The later saved-record/tangent audit and authorized protocol comparison are described above.
No broader geometry guarantee is established; the
restricted dynamic-crab calibration proposal remains unrun. Future work may use two total
threads/workers with a new environment freeze. Further compute and git operations need consent.
Historical launch/recovery instructions below must not restart this completed batch.
The worker `analysis/tests/geometry_campaign.py` prepares exactly 300 geometry-only evaluations
(24 stress cells plus exact-protocol controls × three truths × two scenarios × two crab models),
seed 600500, zero bootstrap. Its documented corpus is `docs/geometry-development-20261006/`.
Scott's further "go" authorizes launch using the stated default one-hour cumulative evaluation
budget (3,600 seconds), up to 300 cases. Do not refill this cap or add cases automatically.
Check `docs/geometry-development-20261006/status.json` before any resume; do not start duplicates
or edit scientific source, runner or frozen input files while it runs. Ten focused offline checks passed.
Initial launch verified: outside-sandbox PID **3557150**, manifest hash
`81f6ff596ed2432d7925fd4fa97bded4492ad33ad0c57a7c525be3667941e97e`, scientific source
`642cbec30013a211b36221b072b6ba63159bceab9ecd439a6bdcfee6a433aafc`, numerical environment
`20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`.
The first evaluation checkpointed with no failure; that is an initial check, not a current count.
The worker needs no network or model calls. Resume only missing cases within the same cap:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/geometry_campaign.py --wall-time-minutes 60 --resume --detach
```

Use escalated execution so the authorized background process survives sandbox exit. A stale
status needs an outside-sandbox PID check, since sandbox process visibility is incomplete.
After `complete` or `budget_exhausted`, review `summary.json` and archived records and update
README/VALIDATION/readiness with measured results; never silently extend the cap.
Publication was completed as `e9a12ea`; further git operations need fresh consent.
The runner freezes its own hash and input hashes in addition to scientific source/environment,
fsyncs successes and failures, conservatively charges interrupted per-case reservations,
enforces a cumulative budget and rejects missing-original-journal resume. Consult its README
for launch/resume; outside-sandbox execution is required for detachment. No full calibration,
validation or additional bootstrap pilot is authorized. Observed-track replay remains pending.

**Latest next-stage work:** Scott said no IMUs are available yet and authorized the suggested
saved-record review, geometry preparation, revised freeze/budget and publication of completed
campaign artifacts. No multi-week calibration/validation budget was authorized. The later
one-hour geometry batch is separately authorized above. Real bench testing remains pending hardware.

Documented new corpus: `docs/research-next-stage-20261006/README.md`, `pilot-comparison.json`,
`geometry-stress-plan.json`, `compute-budget.json`, `calibration-proposed-manifest.json`,
`readiness.json`. Tool: `analysis/tests/prepare_next_stage.py`; tests: `test_next_stage.py`.
It reads both compressed campaigns and both normalized-track archives, performs no fits, rejects
holdouts/replays/overlaps/policy mismatches and preserves source versions. Under the common
10% margin, the first/second pilots have 894/905 eligible flights and 870/884 eligible rank 2;
the first's one diagnostic null rejection remains. Wind/watchdog exclusions persist; do not
disable them or manufacture a zero-rejection claim by dropping development records.

The plan prepares 24 synthetic stress cells, five observed windows and two coverage-blocked
tracks. It proposes 288 geometry-only evaluations (plus 12 exact-protocol controls) but has
not executed them. Observed-trajectory replay still needs integration before running: no actual
IMU, heading/wind, clock accuracy or altitude reference is supplied by a position export.
The synthetic matrix formerly spaced six turns eight minutes apart in 60-minute cases; corrected
to 5/15/25/35/45/55 minutes. All 288 schedules pass the ten-minute/five-minute feasibility rule.

That prospective scientific-source change gives hash
`642cbec30013a211b36221b072b6ba63159bceab9ecd439a6bdcfee6a433aafc`.
Do not mix or resume the completed older-source campaigns under it. The new restricted proposal
has manifest hash `10ee614c1cce1fff9b0f094a0b90659244e30b548d7c9fb4cd3a1e969a3cf168`,
rank 2 / 10% margin / exact 75-minute protocol / SPP / mixed bias and wind, with separate primary
and pairwise endpoints. It is not a broad real-flight eligibility envelope or permission to run.
Goals remain 29,285 accepted calibration and 33,169 accepted validation samples per cell.
Latest point cost: 485,976 attempts / 69 days. Conditional reserve: 560,670 / 80 days, split into
43,830 calibration and 49,615 validation attempts per cell. Bounds assume stable independent
within-cell acceptance; runtime and future acceptance are not guaranteed.

Next: obtain a bounded geometry-development budget, run/check those diagnostics and implement
observed-trajectory replay, review/refreeze the final domain, then obtain a calibration/validation
budget. Fresh calibration and actual frozen primary/pairwise thresholds must precede independent
validation. Keep the stages in `readiness.json` current. No fresh empirical threshold exists.
Verification: 27 focused offline tests passed, complete archive/journal records agree, and the
previous CI fixture fix passed GitHub Actions at `0f1ae60`. Bundle this related preparation and
the completed second-campaign artifacts in Scott's authorized publication commit/push; further
git operations require fresh consent afterward.

**Second pilot complete:** `docs/development-1000-20261006/status.json` is `complete`.
All 1,000 attempts finished in approximately 3h24m, with zero analysis failures, 905 eligible
flights (884 rank 2), 998 valid bootstraps and zero eligible diagnostic null rejections.
Ranks: 936 rank 2, 62 rank 1, two rank 0. The 53 ±10%-cutoff rank flips are all excluded
by the frozen margin. Pairwise three-model outcomes: 888 correct, zero incorrect, 112 abstain.
Do not resume this worker or rerun any completed attempts. The authorized budget is exhausted.

Complete results, journal archives, rank sweeps and magnetic summary are saved locally; the
new corpus README documents the six cells and limitations. README/VALIDATION are refreshed.
At worst rank-2 acceptance 128/166, existing full sample goals imply 485,976 attempts / about
69 serial days before reserve, provisionally. Review the envelope and refresh the frozen
proposal before requesting another compute budget. No thresholds or independent validation
have run, and external-track recovery remains separate, unvalidated analysis work.

The latest completed commit/push is `e9a12ea` (completed pilot, geometry preparation and revised
calibration proposal). The geometry runner follow-up remains uncommitted. Further git operations need fresh consent.
The historical launch/resume instructions below apply only to a genuinely interrupted original
run; they must never be used to restart this completed campaign or treat a missing journal as empty.

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

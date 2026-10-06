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

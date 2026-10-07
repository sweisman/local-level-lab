# Codex preferences for Scott Weisman

## Next archival analysis direction — 2026-10-07

Scott requested one bundled commit/push of the completed work and a path toward analyzing
ILVIS0 on the passenger experiment's physical principle. The staged roadmap is in
`docs/ILVIS0.md`, section "The route from decoded measurements to the proposed experiment's
principle". Start with an archival raw-increment observation adapter and processing/frame
independence checks on geometry-selected files; then test pairwise identifiability before
measured Earth-model fits. Fused navigation is a decoder/context reference, not independent
Earth evidence. Treat GPS geometry, body heading, acceleration, clock and bias assumptions
explicitly. Do not demand a proprietary manual as the sole path to empirical unit validation,
or treat an expected Earth-rate residual as proof of processing independence. Existing
conditional six-file/24-start/200-evaluation limits remain; no new campaign, scientific
promotion or later git operation is authorized by this roadmap. Completed audits stay frozen.

## Completed installation and clock investigation — 2026-10-07

Scott authorized this continuation with "go": inspect logged installation settings and
diagnose the vertical acceleration mismatch in the same six IMU6 representatives. Complete;
PID 4002794 released its lock. No older audit was rerun or resumed, no original deleted,
no scientific gate changed, no Earth fit or git operation performed. All 232 originals remain.

Module `analysis/lll/ilvis0_installation.py`, launcher
`analysis/tests/ilvis0_installation_worker.py`; output `data/ilvis0-installation-clock-20261007/`;
log `data/ilvis0-ready/installation-worker.log`; matching evidence/docs directory. It contains
the manifest, source snapshots, compressed complete report, completion and CSV inventory.
At most two numerical threads. Sources, prior reports and cached matched-sample artifacts
are hashed. Completed studies must not be resumed or mixed with a revised implementation.

All six raw legacy Message 1 setup packets contain candidate angles reproducing the earlier
gyro mappings to roundoff. Serials 2720/3861 use roll/pitch/yaw 0/0/90 degrees; 4126 earlier
0/0/-90, later 90/90/0. The candidate reference-to-IMU offset is .14/.035/-.12 metres in the
five older files and -.194/.240/-.274 in the later one. Legacy 80-byte MSG1 offsets are
EMPIRICALLY INFERRED; the public V6 ICD documents 92-byte MSG20, not these legacy offsets.
The separate structural decoder preserves complete packets, unsupported sizes and tails,
and labels the authority distinction. Samples before the first logged setup are excluded;
later configuration is not assigned retroactively. Recorded setup is not a mount survey.

Full Group-4 header intervals have standard deviations 12.4–13.6 microseconds about 5 ms,
adjacent correlations -.45 to -.56, mean period error <10 ppm and no gaps >7.5 ms. This
supports timestamp jitter around a steady clock but is not independent integration-clock
measurement. Using measured adjacent dt inflated the gravity-related vertical rate noise.
The explicit fixed-200-Hz period hypothesis reduces vertical residual RMS 76–595 times.
At an empirical 3.38e-5 m/s/count velocity-increment scale, 6/6 complete acceleration checks
pass, including unchanged 0.1% scales/correlations/chronological checks. At 0.4 arcsecond/count,
5/6 fixed-period gyro checks pass. The 26 October 2010 file narrowly fails one gyro half:
ratio .99898580935 (outside the unchanged .999 lower limit). KEEP THIS FAILURE. Do not choose
normalization separately by which produces a pass, weaken the threshold, or relabel this
exploratory decoder work as fresh scientific calibration.

Both period normalizations and raw/header values are preserved; no automatic physical
conversion or scientific promotion is enabled. Scale/clock hypotheses are empirical, not a
manufacturer table. The prior failure reports remain unchanged. Simple rigid-body lever-arm
correction worsens all supported comparisons at .2/1/2-second derivative scales for either
sign. The sparse 2017 navigation stream is unsupported for that high-rate correction. Do not
infer that Applanix applies no lever-arm correction from this negative diagnostic.

Thirty focused tests passed (seven new installation/timing tests plus 23 preceding tests),
including corrupt frames, authority/layout distinctions, mounting epochs, clock jitter,
sparse derivatives and interruption-safe resume. No post-restart scans/tests were repeated;
the completed artifacts were checked and documented. Current scientific implementation hash
remains `1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500`.
Next: independently establish integration-clock conventions and the remaining gyro scale
discrepancy, then consider a separately frozen broader per-file decoder audit. Processing
corrections and independent orientation still block Earth-model use. Earlier section counts
and failed diagnostics below are historical, not the current interpretation of acceleration.

## Completed IMU6 units and course controls — 2026-10-07

Scott authorized this continuation with "go": a bounded six-file IMU6 cross-date check
and course-timescale controls. Both are complete, with zero framing/hash/timing audit errors.
No older audit was resumed, no original deleted, no scientific gate changed and no Earth fit
attempted. All 232 originals remain. No git operations are authorized by this continuation.

Units: `analysis/lll/ilvis0_imu6.py`, launcher `analysis/tests/ilvis0_imu6_worker.py`, output
`data/ilvis0-imu6-cross-date-20261007/`, log `data/ilvis0-ready/imu6-worker.log`, matching docs
directory. PID 3943580 completed and released its lock. The initial launcher failed before
creating an audit manifest because legacy inspection metadata lacked `group4_sizes`; this
was corrected and tested against the actual metadata before the successful launch. Do not
resume the completed audit or mix source revisions with its manifest.

Three configurations cover 81 kept IMU6 files. Earliest/latest distinct embedded dates and
source hashes selected six representatives before gyro checks. The empirical gyro hypothesis
is pi/(180*9000) radians/count (0.4 arcsecond/count). Five of six pass with the first date's
mapping frozen; serials 2720 and 3861 reproduce both dates. Serial 4126 changes its relationship
to the fused reference between the 2015 and 2017 recordings. The failed cross-date result is
preserved. The separate cached-sample supplement discovers each mapping on its first half
and tests it on the second: 6/6 gyro checks pass. This supports units and relative mappings,
not an independently established aircraft mount or processing/Earth-rate retention.
Mappings to Group 1: 2720/3861 X=-rawY,Y=rawX,Z=rawZ; 4126 earlier X=rawY,Y=-rawX,Z=rawZ;
4126 later X=rawY,Y=-rawZ,Z=-rawX. Hardware identity alone cannot freeze mounting epochs.
The supplement generator and results are preserved in the units evidence directory; it
checks source/matched-artifact hashes and can be rerun cheaply without rescanning originals.

None of six complete accelerometer checks passes. Horizontal empirical velocity scales are
near 3.38e-5 m/s/count, but no exact velocity conversion or manufacturer scale table is known;
vertical-channel agreement and chronological scale reproduction remain inadequate. Keep
all failures. No complete IMU6 decoder or corpus-wide physical export has been enabled.
IMU6 sensor identity/performance must not be inherited from the different IMU8 reference.
Fitted offsets and Group-1 agreement cannot establish independent Earth-model evidence.

Controls: `analysis/lll/ilvis0_motion_controls.py`, launcher
`analysis/tests/ilvis0_motion_controls_worker.py`, output `data/ilvis0-course-controls-20261007/`,
log `data/ilvis0-ready/course-controls-worker.log`, matching docs directory. PID 3947554 completed
and released its lock. It ran only after the unit worker finished; at most two total CPU
threads. Six strict source scans found five non-overlapping >=3-degree/30-second receiver
ground-track changes in two files, all detected by 2/6/12-second course measurements. These
are recorded route maneuvers, not independent body-yaw truth or broad flight-domain validation.
Thirty-six deterministic, noiseless course pulses (not Earth-model campaigns) show 6/12/16
missed controls at 2/6/12 seconds. All tested corrections lasting >=12 seconds are detected.
A real 0.1-degree, one-second correction is detected at 2 seconds but hidden at 12 seconds.
Do not adopt a longer interval just to recover windows, or call short excursions artifacts.

Both evidence directories preserve manifests/source snapshots/completions/compressed reports.
Twenty-three focused tests passed: eight new units/control tests plus existing motion and
assessment checks, including frozen cross-date mappings/scales and corrupted resume data.
The temporary preflight matched-sample cache created during this continuation was removed
only after comparison with its identical durable compressed artifact; originals were untouched.
Core scientific implementation hash remains
`1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500`.
Next useful work: decode recorded installation/frame settings and investigate the vertical
acceleration discrepancy, then define motion handling that retains sensitivity to short
corrections. No Earth fit or scientific eligibility promotion is justified yet.

## Completed examination of the remaining 61 files — 2026-10-07

Scott asked to examine the 61 kept files without a 60-second fused-motion-compatible span.
The separate local diagnosis is complete; worker PID 3919310 released its lock. Do not resume
the completed audit. No source checksum/framing errors occurred, and all previous native-motion
spans reproduced exactly. No downloads, deletions, Earth-model fits, scientific gate changes
or git operations occurred. All 232 remaining originals stay preserved. Frozen prior studies
remain unchanged and must not be resumed.

Module `analysis/lll/ilvis0_motion_diagnosis.py`; launcher
`analysis/tests/ilvis0_motion_worker.py`; output `data/ilvis0-motion-61-20261007/`;
log `data/ilvis0-ready/motion-worker.log`; evidence `docs/ilvis0-motion-61-20261007/`.
The evidence contains source snapshots, the input/source/environment manifest, completion,
compressed complete report and per-file CSV inventory. At most two CPU threads were used.
Atomic per-file reports and frozen inputs/environment support interruption recovery only
for unfinished runs; a changed implementation requires a new separately identified diagnosis.

Results: 53 files are course-rate resolution sensitive (a diagnostic minute at one or more
of 2, 6 and 12 seconds); 3 also have roll/climb fragmentation; 1 has navigation/receiver
disagreement; 4 yield no minute at any tested resolution. At 2/6/12 seconds, navigation
recovers diagnostic minutes in 39/46/53 files; receiver course alone in 45/49/57. These are
same-file sensitivity comparisons, not independent trials or accepted scientific windows.
Of 43,721 original course excursions, 43,055 lasted under one second (98.5%). All excursions
were under one second in 43 files. Omitting course entirely allows a minute in 58 files.
All 61 exceed instantaneous course somewhere; 54 exceed neither roll nor climb, 3 exceed
climb and 4 exceed roll. The subset comprises 59 IMU6 and 2 IMU21 files. Keep all of them.

The unchanged primary gate is not replaced by these regressions. Averaging suppresses real
small corrections as well as estimator noise; do not label the excursions artifacts merely
because averaging recovers a stretch. No gyro residuals/model-dependent outcomes entered
selection. Missing epochs/gaps remain unsupported. Receiver VTG is ground track, not aircraft
heading or independent orientation evidence. It lacks UTC: use only a unique nearest dated
GGA within 0.5 seconds, retain uncertainty and reject duplicate assignments/invalid/estimated/
manual/simulated modes. Legacy missing mode is explicitly recorded. All 61 files supplied
associated track observations, totaling 29,994 sentences. Native and receiver comparisons
do not resolve IMU units, mounting or instrument corrections.

Tests: eight new motion tests plus seven retention tests passed (15 total), including sustained
turns, north crossing, missing epochs, VTG provenance/timing ambiguity and interrupted resume.
Next useful work: independently validate IMU6 units and mounting, and test a defensible motion
measurement timescale against known real aircraft motion before revising scientific screening.
This examination does not itself authorize a new campaign or Earth-model fit.

## Current 84-file retention resolution — 2026-10-07

Scott subsequently asked to resolve keep/discard for the84GPS-promising, alignment-blocked
files. This authorizes a separate local storage-usefulness audit and discarding proven
redundant copies, superseding the earlier no-deletion instruction only within these84files.
It does not authorize Earth-model fits, synthetic studies, downloads, a relaxed scientific
gate, or git operations. Most of this subset (82files) is IMU6, not IMU21.

Module `analysis/lll/ilvis0_retention.py`; launcher `analysis/tests/ilvis0_retention_worker.py`;
output `data/ilvis0-retention-84-20261007/`; log `data/ilvis0-ready/retention-worker.log`.
The audit checks strict frames/source hashes, raw IMU completeness in independently chosen
GPS windows, and fused motion/uncertainty as labeled context. Unknown scales, fine alignment
and failed reference fits alone are never grounds for deletion. Storage retention does not
establish independent Earth-science usability. Two CPU threads maximum; no duplicate workers.
The source/input/environment manifest and per-file atomic results support safe resumption.
Completed; PID3885532 has released its lock. Do not resume the completed audit. Decision:
keep83files and discard1byte-identical duplicate. All83keepers have at least60seconds of
complete raw IMU inside GPS-selected stretches. Of them,22have a60second motion-compatible
span in fused context (diagnostic, without a new bank-boundary buffer or scientific promotion).
The other61remain useful raw/route recordings for investigation; steady level attitude is not
established. The83keepers comprise81IMU6 and2IMU21 files. Unknown orientation/corrections
remain scientific blockers. All84strict hash/framing audits passed; no Earth fit or gate change.
The redundant22April2010original was removed after verifying both current uncompressed
hashes and journaling prepared/removed dispositions. Reclaimed6984885bytes (~6.66MiB).
Current stored originals:232 (80previous candidates+152alignment-blocked). Historical catalog
dispositions are93no-level rejections plus1later duplicate removal; old ledgers are unchanged.
Source snapshots, manifest, completion, full report and human-readable CSV inventory live in
`docs/ilvis0-retention-84-20261007/`; durable cleanup journal is in its matching data directory.
Future source selection MUST honor that journal and map the removed task to its canonical
copy. Older frozen assessment/follow-up workers must not be restarted with233expected files.

The removed pair was byte-identical: task1fec3d39099d0e619100(2010-04-21catalog) and
task70d727f23a7df6b2e47f(2010-04-22catalog). Both embedded dates are2010-04-21. Keep the
correctly dated canonical original. The duplicate removal verified both current
uncompressed hashes. Durable prepared/removed records and fsync preserve interruption recovery.
Never delete unowned paths, supplied originals, or nonidentical/unresolved evidence.
Completed prior workers remain frozen and must not be resumed, especially after deduplication;
future source selection must honor this audit's cleanup journal/canonical task mapping.

Focused tests:7new retention tests, including corruption protection and interrupted deletion
recovery, plus7assessment tests passed (14total). An initial IMU6 diagnostic shows a90degree
horizontal axis remapping improves gyro correlations above0.999998 in one sample. This
explains some failed same-axis comparisons; it is not yet a validated IMU6 physical decoder.

## Current IMU21 / alignment assessment — 2026-10-07

Scott authorized this separate local assessment with "yes proceed": independently test IMU21
scales/axes, inspect internal navigation uncertainties, and screen unresolved originals using
GPS-only geometry. No new downloads, deletions, synthetic campaigns, Earth-model fits or git
operations are authorized by this assessment. Keep all233 remaining originals. The completed
acquisition/follow-up/continuity evidence below remains frozen; do not resume those workers.

Module: `analysis/lll/ilvis0_assessment.py`; launcher:
`analysis/tests/ilvis0_assessment_worker.py`. Output:
`data/ilvis0-imu21-assessment-20261007/`; evidence/documentation:
`docs/ilvis0-imu21-assessment-20261007/`. A separate source/environment/input manifest,
process lock, atomic per-file results and status permit interruption-safe resumption. At most
two total CPU threads. Check `status.json` and the worker lock before launching/resuming;
an active local worker needs no model calls or network. Its log is
`data/ilvis0-ready/assessment-worker.log`. Launch outside the per-command sandbox if needed
for the authorized worker to survive command/chat disconnection.
Completed; PID3782131 has released the process lock. Do not resume this completed assessment
or mix revised source into its manifest. All233 context checks passed. Of98IMU21 files,71pass
physical checks;3of6exact configurations reproduce both preselected dates. Serials3861,3894
and6448pass;3456,5680and7763each fail one selected date. Serial3894reproduces Y/Z sign
reversals. Keeping both configuration and per-file gates yields24native-axis physical-window
exports totaling10068.853s (167.8minutes) across possibly overlapping streams. Combined with
the earlier4IMU8 candidates,28files have supported physical units and12013.949s (~200minutes).
All27per-file failures remain recorded; failed representative dates were never replaced.
GPS-only potential windows occur in84of153unresolved files, totaling25718s across streams.
All153remain scientifically unresolved and all233originals remain. There were0eligibility
changes, deletions or Earth-model fits. Group2counts:102926inferred legacy76-byte packets,
18253documented V6 packets. These are fused internal estimates, not independent accuracy.
Final evidence: assessment `completion.json`, `summary.json.gz`, manifest/source snapshots;
guide/README/readiness updated. Next: diagnose failed physical checks and independently
establish processing/orientation; no Earth fit is justified by decoder agreement alone.

Frozen IMU21 candidate scales are2^-28rad/count and0.3048*2^-21m/s/count (binary feet/second
increments converted using the exact metre/foot relation). These are empirical hypotheses,
not a discovered manufacturer scale table. Choose representative files by existing geometry,
actual embedded dates and distinct uncompressed hashes. Freeze the first file's gyro-derived
axis/sign mapping; require it on the other date and use the same mapping for acceleration.
Preserve the existing correlation,0.1%scale and chronological stability requirements, report
failures, and never reselect a configuration's representatives because its gyro check failed.
Only export native-axis raw/physical windows after two-date configuration and per-file checks.
Fine-alignment dynamics can support decoder diagnostics but never scientific eligibility.

Group2 has76-byte legacy and88-byte V6 layouts. The legacy nine-float uncertainty prefix is
explicitly inferred; the modern layout is documented. Preserve payloads and unsupported
sizes. Internal fused RMS estimates do not independently prove attitude accuracy. GPS-only
windows use checksummed positions/heights and documented local regressions; they cannot
establish roll, mounting axes, alignment, or short maneuvers. They are potential geometry,
not accepted level-flight scientific data. Scientific gate changes and Earth-model fits remain0.

Verification before launch:25 focused parser/follow-up/continuity/assessment tests passed.
The first real IMU21 file closely matches the candidate scales but fails one gyro-half scale
stability check; that failure must remain in the results. Do not call all IMU21 decoding solved.

## Current ILVIS0 acquisition/decoder handoff — 2026-10-07

Scott authorized implementation of the `.013` parsing/acquisition plan, independent physical
validation, a six-file cross-date compatibility trial, and later corpus screening/retention.
This supersedes older statements below that physical units must remain opaque until a
manufacturer table arrives. It does not authorize rerunning frozen synthetic studies.
At most two total CPU threads. No new git operation is authorized.

Reusable modules: `analysis/lll/applanix.py`, `ilvis0.py`, `ilvis0_acquisition.py`.
Legacy `analysis/tests/inspect_ilvis0_sample.py` and its original data artifacts are preserved.
The reference independently supports six signed int32 increments, scales2^-14m/s/count
and2^-18rad/count, expected axes/signs, and chronological holdout scale checks. Group1 is
fused navigation and is only a decoder/motion reference. Processing/correction independence
remains unresolved; no ILVIS0 Earth-model fit or synthetic decision threshold has been applied.

Evidence: `docs/ilvis0-physical-validation-20261007/`; guide `docs/ILVIS0.md`.
Catalog:326 .013 files,4061.18612 roundedMiB,2009-04-14 through2017-09-20. Catalog filenames
are a documented corpus; do not enumerate unrelated Downloads or credential paths.
Reference:13,086,748bytes,143,471frames,132,444Group4,662Group1,5934Group10001,
660validGGA/VTG/ZDA each, zero outer checksum failures. It has no qualifying60s level window
under the frozen geometry screen. Only newly generated owned bulk derivatives were discarded;
the user's original and historical corpus remain. A1000-row excerpt is regression evidence.

Current owned resumable corpus: `data/ilvis0-ready/`. The initial `data/ilvis0/`,
`data/ilvis0-v2/`, and `data/ilvis0-current/` contain development ledgers from parser refinement/authentication checks;
they are stopped, not campaigns to restart. Their sources differ from current code.
The latest source/environment/catalog freeze lives in the current corpus manifest.
`records.jsonl` is append-only/fsynced and includes every catalog task; `inventory.json`
and `status.json` summarize it. Never mix source revisions under an old manifest.
If source changes, start a separately named owned corpus and preserve historical provenance.

The six-file trial consists of the supplied ATM2009-04-14 reference plus:
ATM2009-04-16; LVIS5102010-10-28; POS5102012-05-10; LVIS6102015-10-29;
the2017-09-20 filename containing610p4965. Actual filenames/URLs are in the catalog.
The six-file trial completed: two retained, three unresolved, one confirmed no-level rejection;
physical decoding passed for the two ATM dates. Retained geometry totals626.31seconds, but
only the2009-04-16 ATM file currently has both retained geometry and accepted physical units.
Other IMU types/configurations remain unresolved and are not assigned IMU8 scales.
No standard `.netrc` existed when checked. User first chose browser downloads,
then cancelled manual downloading and asked for automated HTTPS/S3 acquisition. Current
one-time setup can use `configure-auth` locally with a hidden Earthdata token prompt.
The user instead supplied an Earthdata session cookie and explicitly authorized its use;
it is passed through hidden stdin to a worker and held only in memory. No credential has
been placed in code, command-line arguments, reports or evidence. Never reproduce it in
documentation or inspect browser/unrelated credentials. Standard `.netrc` still did not exist
at the last check. Do not assume the "Configured" response meant a credential file was created.
NSIDC S3 is restricted to authorized AWSus-west-2 environments; use authenticated HTTPS here.
Do not launch cloud infrastructure or incur paid compute.

Full326-file acquisition/screening completed in `data/ilvis0-ready/`; PID3725303 has released
the worker lock. Final counts:18retained,58confirmed no-level rejections,250unresolved originals
kept. There are22retained windows totaling7329.62seconds across files, which may include
simultaneous instrument streams rather than independent flights. Two retained ATM files have
accepted physical decoding, totaling692.01seconds of qualifying geometry. Three files overall
passed physical validation, including the no-level reference. No Earth-model fit has run.
Completion evidence: `docs/ilvis0-physical-validation-20261007/corpus-screening.json`.
Read-only unresolved diagnosis:114files have GPS-time-tagged IMU logs (unsupported by the
UTC-only screen),136have UTC tags but insufficient valid navigation/GPS context;16of the
latter have some valid context. See `unresolved-diagnosis.json` in the same evidence folder.
Next: verified GPS-to-UTC mapping, full navigation alignment/context audit, and independent
physical checks for each configuration. Preserve the completed corpus manifest/ledger;
revised decoding belongs in a separately frozen follow-up, without new downloads or synthetic
campaigns. Do not relax alignment/physical checks merely to increase accepted counts.

Scott authorized that follow-up with "go" and additionally requested performance
characterization against flight speed. It completed in `data/ilvis0-followup-20261007/`;
PID3743058 has released its lock. Launcher: `analysis/tests/ilvis0_followup_worker.py`. This is a local audit of268
preserved originals (250unresolved+18retained), not new flight attempts or Earth-model fits.
Module: `analysis/lll/ilvis0_followup.py`; it verifies original uncompressed hashes, strict
frames/checksums, dated GPS/UTC leap offsets against embedded ZDA and available dual tags,
and retains the original geometry/alignment thresholds. It selects at most two different dates
per exact observed firmware/IMU/rate configuration for physical channel diagnostics. Fine-
alignment dynamics can support labeled decoder diagnostics, never scientific eligibility.
For qualifying windows with independently passing units, it reports observed gyro variability
and quantization at1/10/60second averaging. Aircraft motion remains included in those statistics.
The modeled horizontal transport scale uses measured speed/latitude/altitude; it is a prediction,
not a measured Earth signal. Current core default IMU8 validation remains conservative.
Follow-up status/manifest and per-task JSONs live in that separate corpus; recovery skips finished
steps and rejects source/environment/old-ledger changes. Do not resume the completed study
or mix revised source under its manifest; any next decoding work needs a new follow-up freeze.
Final counts:80candidate files (62newly recovered),35new no-level classifications,153still
unresolved due to alignment (133fine throughout,2earlier stage,18mixed full/fine;1also GPS).
All268 timing checks passed. There are108candidate windows,33387.17seconds across possibly
overlapping instrument streams. Eleven exact configurations were tested; two IMU8 configurations
reproduced scales on two dates each. Four usable files passed physical checks,1945.10seconds
(32.4minutes). Other IMU types failed the IMU8 scales and were not converted. IMU21 correlations
often remain high at different freely fitted scales; one configuration has Y/Z sign reversals.
Those findings support a separate layout/scale/axis investigation, not automatic conversion.
After the completed audit and continuity check, Scott asked about deletion. Under the standing
instruction to discard confirmed rejections,35new no-level owned compressed originals were
removed after verifying uncompressed hashes and fsyncing prepare/remove dispositions. This
reclaimed208952434bytes;93confirmed rejected files total. Keep all80candidate files and153
unresolved originals. The original screening ledger/reports remain immutable; later storage
dispositions are in `data/ilvis0-followup-20261007/cleanup.jsonl`, with completion evidence in
both that corpus and `docs/ilvis0-followup-20261007/cleanup-completion.json`.
Future work must honor that cleanup journal rather than expect the35old-ledger unresolved
originals still to exist. Do not rerun completed follow-up/continuity studies unchanged: the
verified partial-overlap pair was among the35later discarded no-level files, and its complete
reports remain as evidence. Completion evidence: `docs/ilvis0-followup-20261007/`.
Current speeds140–256m/s predict horizontal transport4.5–8.3deg/hour. One-minute observed
body-axis standard deviations5.7–21.7deg/hour include aircraft motion and few blocks, not an
intrinsic gyro noise spec. Processing independence/orientation still block Earth-model fits.
Original parser/acquisition/decoder source snapshots matching the initial manifest are in
`docs/ilvis0-physical-validation-20261007/source-freeze/`; follow-up source copies are in the
new evidence folder's `source-freeze/`. No new git operation was authorized.

Scott also requested checking whether level-flight stretches cross file boundaries. Completed
via `analysis/lll/ilvis0_continuity.py`, with4focused tests. All326file spans were grouped by exact
instrument configuration and dated using embedded ZDA, not catalog filenames alone. Four pairs
overlap:3are byte-identical duplicates (one has different catalog dates),1is a verified partial
overlap with130221exactly matching IMU packets. Its deduplicated navigation/GPS union adds16.73s
but still has no qualifying window. No qualifying stretch was lengthened; the nearest separated
same-instrument pair has1111.34s missing data. No interpolation, fabricated series or original
file deletion occurred. Evidence: `docs/ilvis0-followup-20261007/file-continuity.json`.
Next empirical configuration studies must select distinct original hashes and actual embedded
dates, rather than treating different catalog dates or filenames as independent repeats.
Focused verification:30ILVIS0 tests passed, then7follow-up tests (including new persistence)
passed. This is31distinct tests, not37. No synthetic studies or Earth-model fits were run.
The frozen corpus is complete; do not restart it or mix a revised decoder into its manifest.
The former daemon used an in-memory session; the finished process no longer holds that credential.
Future recovery helper: `analysis/tests/ilvis0_worker.py --full --detach`, with optional
`--session-cookie` hidden input when renewed session authentication is needed. It checks the
process lock. Launch outside the per-command sandbox so it survives disconnection.
The helper was added after launch; the completed worker used the original in-memory driver.
Completion compacted18redundant full physical CSVs after checking compressed originals and
qualifying physical/raw IMU windows exist, with durable `storage.jsonl` disposition records.
Focused verification before launch:24ILVIS0 tests plus9persistence tests passed; no synthetic
campaigns or Earth-model fits were run. The new recovery helper has not had an end-to-end test.

Resume after local authentication is configured:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 /home/sweisman/venv/bin/python -m lll.ilvis0_acquisition batch --catalog docs/ilvis0-physical-validation-20261007/catalog/catalog.json --output data/ilvis0-ready --reference /home/sweisman/Downloads/ILVIS0_gyro_54935_atm_applanix_14Apr09.013
```

Network execution requires sandbox escalation if blocked. No need to re-request scientific
authorization for this same trial. `--local-only` can process the supplied reference without
network/auth, leaving the other five pending. `--input-dir` reads only exact catalog filenames.
Full acquisition required independently accepted physical checks on at least two dates, now
achieved by the ATM trial. Each new configuration is still tested per file. Trial evidence is
`docs/ilvis0-physical-validation-20261007/six-file-trial.json`.

Latest user retention rule: discard confirmed no-level files after durable hash/reason records;
keep ALL useful and unresolved originals. This supersedes the earlier six-exemplar quarantine
cap. Missing/ambiguous GPS or unknown layouts are unresolved, never evidence of no level flight.
The current tool deletes only owned copies/derivatives, never supplied Downloads or historical
sources. At least60contiguous seconds after10s maneuver buffers are retained; speed>=50m/s,
|vertical speed|<=1.5m/s, |course rate|<=0.05deg/s, |roll|<=5deg, GPS/nav gaps<=2s.
Screen policyilvis0-level-v2 also requires95% valid GPS/motion context before a no-level
rejection; missing/ambiguous time mappings remain unresolved. UTC time1 mapping must be
documented by the packet header; POS time is not silently rounded into a receiver UTC fix.
Flight selection must precede Earth-dependent gyro residual inspection.

Any later empirical Earth-shape comparison remains separate and conditional on independent
processing/orientation and useful geometry: at most six geometry-selected files,24optimizer
starts including interrupted starts,200evaluations/start. No bootstrap/calibration or winner
claim. If independence/identifiability is unresolved, document the blocker rather than fit
fused navigation as science. Expanding Earth-model analysis beyond that allowance needs a
fresh finite scope; corpus inventory/download/parser screening are not synthetic campaigns.

## Who you're working with

The user is **Scott Weisman** — not Stephen, not Steven. GitHub `sweisman`,
email sweisman@gmail.com (a handle; do not infer a first name from it).
Always use "Scott" in copyrights, licenses, attribution lines, signed
correspondence, and anything else user-facing.

## Token economy

Scott works against tight token / plan-session budgets. Wasted tokens cost real work.

- The concern is model-token consumption, not local CPU time. Prefer sufficient automated
  computation to repeated small probes, lengthy explanations or frequent model-driven polling.
- Use focused verification when it answers the question; run longer local checks when needed.
- Don't re-read a file just edited; trust successful edits.
- Keep replies tight and lead with the result.
- Ask before unusually token-intensive investigations or multi-agent fan-out, naming the
  expected token cost. Do not ask solely because a local build, test suite, numerical sweep
  or other authorized computation takes CPU time. A full numerical evaluation is not itself
  a token-intensive re-derivation.
- Use bounded output and durable results so a local job can finish without consuming model
  tokens throughout its runtime. Avoid arbitrary tiny compute caps that force extra turns.
- One careful pass beats iterative polishing that wasn't requested.

Clarified on 2026-10-07: these rules supersede earlier CPU-time-based approval requirements.
The two-thread ceiling, explicit campaign attempt limits, frozen scientific scopes, paid or
external resource approvals, git consent and production-promotion requirements remain intact.

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

## Latest continuation — 2026-10-07

**Completed authorized replay (supersedes earlier progress statements below):** Scott said
"go" after the proposal to replay the partial ORD–LAX control under three truths, both wind
models and combined wind/IMU drift. Exactly six development analysis attempts are now frozen
in `docs/observed-pair-replay-20261007/plan.json`, prepared by
`analysis/tests/prepare_observed_pair_replay.py`. Fresh shared seed600910; scenario
wind+bias_mixed; window3600–10800s; turns5/15/30/40/90min; matched forward reference;
dynamic bias; complete nonlinear fits/direct pair profiles; zero bootstrap. Two workers,
one numerical thread each. Planhash ec543811c717ad0948a0ec89815099cd2c0589ddf04464d45730c13f8564802a;
science hash unchanged1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500.
Corpus and resume instructions are in that directory's README. Worker state is in
`run/status.json` and `run/shard-000.status.json` / `run/shard-001.status.json`; inspect
before any launch/resume. No scientific source edits while active. Started attempts,
including failures/interruption, are spent; resume missing tasks under the same total6.
Launch/resume detached workers outside the sandbox to survive tool/chat disconnection.
It is now complete: all6attempts,0failures,6converged,335.204wallseconds,
376.529summed attempt-seconds. No active workers; do not resume or rerun. Each retained99cruise
minutes, adequate headings and6epochs; globalrank1; reported forwardσ0.392–0.572deg;
no watchdog-excluded segments. Rotation and stationary-globe/disc pairwise gates pass6/6
under both candidates; rotating-globe/disc passes0/6, so primary3-model eligibility fails.
Allpairwise decisions abstain: zero bootstrap/no empirical thresholds. No calibrated winner.
`review.json`, `noise-review.json`, `verification.json`, `SUMMARY.md` in the new corpus
preserve the assessment. New readonly helpers: `analysis/tests/review_observed_pair_replay.py`
and `analysis/tests/audit_replay_noise.py`. Matching fitter inputs were independently checked
identical across23fields within each truth; plan/source/input/environment/task identities match.
Residual-based gyroσ is38.28–38.36dph versus planning3/6dph. Target planninginformation27–41
versus actual free-weighted0.52–1.36; profileSD0.62–0.64 for endpoints one unit apart.
These residual scales include sensor/process/model error and are not real-device measurements.
Saved-data diagnosis is complete: `analysis/tests/audit_replay_residuals.py` independently
reconstructs the assumed attitude/motion with SciPy and evaluates saved parameters without
synthesis or solving. Report: `docs/observed-pair-replay-20261007/residual-decomposition.json`.
Final residualRMS39.23–39.29dph; motion mismatch39.63dph; sensor/calibration remainder about3.9dph;
science/orientation mismatch about1.1dph. The dominant false correction is38.12dph: changing
specific force is treated as changing gravity/IMU tilt. Reconstructed apparent-up matches
saved up within0.0035deg; apparent/true-up can differ2.52deg. True-plumb diagnostic substitution
leaves about12dph without refitting; simulator truth is never an operational correction.
Components are correlated; preserve their second-moment matrix and do not add independent
variances. Three independent physical/bin/gap tests pass. No scientific source changed.
That research-only observed-data prototype is now implemented and tested:
`analysis/tests/acceleration_motion.py`, `review_acceleration_motion.py` and
`test_acceleration_motion.py`. Corpus `docs/acceleration-motion-20261007/`; current results
in `support-corrected/review.json`, arrays and `verification.json`; initial run/source preserved.
Correction uses saved GPS/raw acceleration/recovered epochs/forward, never prescribed truth;
truth enters a separate posthoc scorer only. Policy observed-acceleration-motion-development-1;
production/decisions disabled. FrequentGPS≤2s, common Hann force/velocity filtering, iterative
gravity solve, high-rate frame differentiation then bin integration. Never bridge gaps/turns.
Exactly93states/case:81filter/crab-angle/crab-rate/forward states plus12marginal-σ controls.
All6cases complete,0failedstates; nominal85minutes, common83. Same85-minute residualRMS
33.75–33.89to11.12–11.20dph with saved model parameters fixed; motionerror10.05–10.12dph.
Sensitivity residuals9.6–37.3dph on common83minutes; do not select a favorable truth-scored
state or claim power/coverage. GPS/force marginal propagation assumes independent errors;
full correlations/instrument systematics/Coriolis-curvature acceleration bounds remain open.
Initial six global state failures were corrected to local out-of-envelope support exclusions,
without changing1.5m/s² limit. Eleven focused tests pass. No scientific production source,
frozen campaign, eligibility or decision changed;0newflights and0optimizer calls.
That joint research prediction is now implemented in `analysis/tests/joint_acceleration_motion.py`,
with `test_joint_acceleration_motion.py` and `review_joint_acceleration_motion.py`. It inherits
the existing wind/TAS and bias parameterization but recomputes gravity/motion/science at each
wind/forward/error state. Six coherent marginal-error modes have unit Gaussian priors; full
measurement-error coverage remains unvalidated. Fixed observable support83minutes; state
changes cannot select rows. All six reference checks pass; reference residuals~11dph (wind)
and~15dph (wind_tas), local-curvature diagnostics only. Sixteen focused checks pass.

Latest "go" authorizes the bounded saved-recording joint nuisance refits: exactly the six
existing cases, free + three fixed-model fits, at most one predefined free restart per case
for nesting. Maximum30optimizer calls includes interruptions; max_nfev200; no bootstrap,
new flights, calibration or decisions. Corpus `docs/joint-acceleration-motion-20261007/`,
with frozen scope in `refits/plan.json`; current progress in `refits/status.json`; append-only
fsynced starts/completions in `refits/attempts.jsonl`; atomic per-fit checkpoints/hashes;
`run.lock` prevents duplicates. One numerical thread; up to one other test worker fits the
two-CPU ceiling. **Read status before any resume and do not edit its frozen scientific/helper
sources while active.** README documents the command and corpus. Resume missing fits only,
preserve interrupted starts and the30-call limit, reject source/environment changes.
No duplicate worker or re-authorization is needed for this already authorized finite scope.
When complete, assess convergence/nesting/residuals/boundaries separately from raw objective
differences; those are not calibrated rejections. Update docs/status before any consented git.
**This scope is now complete:**6cases,24started/completed optimizer calls, all converged and
nested,0repairs,0boundaryflags; no active worker or missing work. Do not resume or use the
unused6-call reserve for additional fits. ResidualRMS7.92–8.57dph on fixed83minutes;
sumcompletedoptimizer309.864s (not measured wall time). `refits/review.json` and
`refit-assessment.json` preserve results/checkpoint hashes/fit boundaries. A completed-scope
resume check skipped all fits with no extra optimizer call. Sixteen focused checks pass.
The next saved-data bandwidth/covariance scope is also complete:
`analysis/tests/matched_measurement_motion.py`, `review_matched_measurement_motion.py`,
`assess_matched_measurement_motion.py`, `test_matched_measurement_motion.py`;
corpus `docs/matched-measurement-motion-20261007/` (README,review,sixNPZ,verification).
Exactly6readonly saved-free-fit comparisons,0optimizercalls/newflights/bootstrap. One numerical
thread; no active worker. Joint GPS/force retain30sHann; additional identical30sHann filters
the gyro and complete reconstructed prediction before minute integration. Common support79
of83minutes; regridded residual7.85–8.32→7.08–7.48dph (~9–10% reduction). Motion reconstruction
closes exactly; slow science/bias lift within uninterrupted epochs changes0.026–0.040dph.
This is a diagnostic interpolation, not a continuous refit-ready observation equation.
Full gyro-only time/axis covariance propagates independent one-second empirical mean errors,
filter overlap and rotations; marginalRMSsigma~3.53dph includes within-second aircraft motion.
Residual adjacent-minute correlations reach−0.61; nuisance fitting can induce correlations,
so these do not identify an error source or establish significance. Hash-bound artifacts,
independent residual/PSD checks and21focused tests pass. Completed corpus and bound helper
sources are immutable; do not rerun/overwrite. Next develop a continuous consistently filtered
measurement equation and propagate shared GPS/force/gyro errors plus fit-induced covariance.
**That scope is now complete:** `analysis/tests/continuous_measurement_motion.py`,
`review_continuous_measurement_motion.py`, `assess_continuous_measurement_motion.py`,
`test_continuous_measurement_motion.py`; corpus `docs/continuous-measurement-motion-20261007/`
(README,plan,status,run.lock,6caseJSON/NPZ,review,verification,failedpreflightplan/status).
Exactly6saved-free-state evaluations,0optimizer/newflight/bootstrap; no active worker.
All prediction terms evaluated at GPS times, fixed79minutes,30sinput/additionaloutputHann.
ResidualRMS7.0763–7.4782dph. Eleven-channel shared covariance preserves GPSvelocity cross
terms and time-matched6×6IMU blocks plus physical wind constraint cross covariance. IMU
matches unique/same-second/epoch≤0.1sampleperiod; unmatched samples retain mean scaling.
Initial strict equal-timestamp preflight failed before evaluation; historical plan/status
are not an active/resumable campaign. Independent-second sigma11.2533–11.2722dph (~90%
varianceGPS); local old-weight deterministic-penalty response residualsigma11.1343–11.1603.
This is saved-state sampling propagation, not a refit/posterior/validatedcoverage.
Accuracy scales/missing correlations, mount/forward/calibration/instrument/acceleration/
filter uncertainty remain open. Six hashed checkpointed cases complete,93.203summedseconds;
resume skipsall6. Independent full-input direction≤1.523e-9relative; directleast-squares
response≤1.687e-14; PSD/component checks and29focused tests pass. Completed corpus and
bound helper sources are immutable. Next test time-correlated GPS/IMU error sensitivity
before choosing weights or defining further finite matched refits. Production unchanged.
**Temporal sensitivity is now complete:** helpers `analysis/tests/temporal_measurement_covariance.py`,
`review_temporal_measurement_covariance.py`, `assess_temporal_measurement_covariance.py`,
`test_temporal_measurement_covariance.py`; corpus `docs/temporal-measurement-covariance-20261007/`
(README,plan,status,run.lock,6caseJSON/NPZ,review,verification). Six saved states×36combinations
of GPS/IMU correlation durations0/1/5/15/60/300s,216scenarios, fixed79minutes and marginalscales.
Standardized principal correlation roots preserve same-second covariance; IMU latent errors
follow physical sensor axes across recovered mounting rotations. Exact elapsed-time exponential
recurrences carry covariance across gaps without adding observations/filter/derivative support.
Fixed-state sigma11.2533–42.3085dph; local old-weight deterministic-penalty residualsigma
11.1343–40.6480dph; largest residual scale GPS15s/IMU300s in all6. Conditional scienceSD
can exceed1; these are assumed sensitivity scenarios, not characterized hardware, calibrated
bounds, posterior intervals or new fits. No scenario is selected as a decision assumption.
Six checkpointed evaluations67.803summedseconds, one numerical thread,0optimizer/flights/
bootstrap/activeworkers. Completed resume skipsall6. Baseline recovery≤5.240e-15relative,
dense240-time kernel≤3.444e-12; PSD/all216summary checks and34focused tests pass. Corpus/bound
sources immutable. Next implement and verify a covariance-aware research objective including
shared GPS auxiliary errors before separately scoping further finite matched refits.
**The full-covariance objective scope is now complete:** helpers
`analysis/tests/covariance_measurement_objective.py`, `review_covariance_measurement_objective.py`,
`assess_covariance_measurement_objective.py`, `test_covariance_measurement_objective.py`, plus
`wind_constraint_discrepancy.py`, `review_wind_constraint_discrepancy.py`,
`assess_wind_constraint_discrepancy.py`, `test_wind_constraint_discrepancy.py`.
Corpus `docs/covariance-measurement-objective-20261007/` and `wind-discrepancy/` child;
Each hasplan/status/run.lock/6caseJSON/NPZ/review/verification; parentREADME explains both stages.
216measurement-only saved-state checks plus216explicit registered-discrepancy checks,
fixed79minutes,0optimizer/newflight/bootstrap/activeworkers. Frozen joint whitening retains
cross blocks and residual signs; logdet separate, singular covariances fail without
jitter/clipping. Existing2m/s physical wind allowance retained as normalized auxiliary
variance1 in addition to propagated measurement covariance; no truth/data tuning.
Physical-wind quadratics~27,718–598,005measurement-only vs167–336with allowance; broad-wind
controls unchanged. No significance/winner/covariance choice follows.44focused tests;
independent objective/direction/local-response checks pass,54.164+7.093summedseconds.
Completed resumes skip allcases. Completed corpus/bound sources immutable; no production
science/eligibility/decision changed. Covariance remains provisional/free-state-linearized.
Next finite scope authorized by Scott's 2026-10-07 "how much is left? go":6saved cases×correlation
pairs(0,0),(15,15),(300,300),(15,300)s×free+3fixed=96primaryfits, at most24predefined nesting
repairs,120starts including interruptions; max_nfev200. Freeze covariance per comparison,
retain registered discrepancy, no bootstrap/newflight/calibrated decisions.
Worker `analysis/tests/refit_covariance_measurement.py`; corpus `docs/covariance-refits-20261007/`.
Five focused solver/derivative/recovery checks passed before launch. The scope includes
checkpoint/resume and convergence/nesting/boundary assessment. Source/environment freezes,
fsynced journal and archives, and a process lock protect continuation. One numerical thread.
Read status.json before resuming; use the command in the corpus README. Detached launch
must survive command/chat disconnection (outside the command sandbox when required).
Do not edit frozen helpers or original scientific source while this worker runs.
Completed optimizer failures/nonconvergence are retained; never rerun them. Interrupted
starts count against120; interrupted single nesting repairs are not repeated. No new
compute-budget question is needed for the unfinished portion of this authorized scope.
**This covariance-refit scope is now COMPLETE and its authorization spent.** Launch
succeeded outside the command sandbox; actual historical PID/command are in launch.json.
The six cases are three underlying simulated recordings, each fitted with two wind
candidates, not six independent flights. All96primaryfits converge;24comparisons nest;
0repair/interruption/failure;0boundary or1%-near-bound fits. Optimizer1732.595s,
launch-to-completion30.473minutes, including independent audit31.301minutes. No active
worker, newflight/bootstrap/calibration/decision/production change. Free residualRMS
4.4711–9.8778dph. Injected model has lowest fixed objective throughout; these shared
recordings are not24independent successes or calibrated winners. Longer error persistence
weakens differences strongly. Local unpenalized pair retention23.5–52.4%rotation/still,
4.0–14.3%rotation/disc,31.7–64.3%still/disc; no gate threshold applied. Rotation/disc
remains the weakest contrast. Independent residual/objective/direction and covariance/
support/bounds/journal checks pass. Complete resume skipsall24cases,0additionalstarts.
The unused24repair starts do not authorize more fits. Final results/verification are
in the corpus; completed helpers/checkpoints are immutable. Resume an interrupted
scope only, never reanalyze these completed fits to improve evidence.
Independent audit helper `analysis/tests/assess_covariance_refits.py` waits for completion,
checks full-equation residual/objective/direction arithmetic, fixed support/covariance,
start limits, convergence, nesting and boundaries, and records uncalibrated local pair
projections. Its two closed-form projection tests pass (17focused checks including the
solver/objective/discrepancy controls). Audit never performs additional optimizations.
Its foreground waiting process may stop on chat loss; restart it with the README's
environment and `analysis/tests/assess_covariance_refits.py --wait`, or run without
`--wait` after the worker completes. Do not resume a complete worker just to assess it.
If interrupted between durable fit metadata and journal completion, retain the fit:
the audit identifies a completed checkpoint without a completion event separately
from an interrupted optimizer. Do not rerun it to fill the journal.
Next characterize actual hardware/GPS persistence and verify the motion correction,
then define a defensible research-candidate covariance domain and informative protocol.
Partial pair/shape evidence remains useful; no three-model protocol has been established.
Fresh calibration/independent validation remain separate, expensive and unauthorized.
Further refit/bootstrap/replay campaigns require a new finite scope. Scott authorized
one bundled commit/push of the completed continuation on2026-10-07. Precommit verification
passes54focused checks across11new test files. That consent covers this logical unit only;
subsequent continuation changes need fresh git consent. Confirmation of the pushed
commit will be recorded during the next continuation.

**Bundled commit/push confirmed:** `ed47605`, pushed to `origin/main` on2026-10-07.
It contains the completed observed-route/motion/covariance studies and96refits with
their frozen evidence. Precommit54checks pass; that commit/push consent is spent.
The post-push continuation prepares hardware input-persistence diagnostics:
`analysis/tests/characterize_input_persistence.py`, `test_characterize_input_persistence.py`,
and `docs/INPUT_PERSISTENCE.md`, with bench/README/validation/plan documentation.
Nine focused controlled tests pass using at most2numericalthreads. No real-device
input, newflight/refit/bootstrap/calibration/validation or production science changed.
It reports still-phase second means, IMU/GPS/shared covariance, lag and averaging
diagnostics under two detrending views, preserving gaps and saturation exclusions.
No noise model, covariance domain, qualification or threshold is selected. Still
GPS behavior is not airborne GPS characterization. Keep original recordings; output
refuses overwrite. These new continuation changes are uncommitted and need fresh
git consent. Next obtain the actual still/motion controls described in the guide.
The old gyro weights, six coherent error modes and conditional GPS/TAS likelihood remain
provisional. No power, calibrated rejection, winner or promoted gate follows from these checks.
Further refit/bootstrap/replay campaigns need separately defined scope; no new flights are authorized.
Six-flight authorization is spent. All continuation work remains uncommitted; git consent
is required for the next commit/push. Token consumption, not routine local CPU time, is the constraint.
No bootstrap campaign, empirical calibration, validation, promotion or git operation is
authorized. CPU time alone is not a reason to ask for approval again. This replay authorization
persists through interruptions; do not request it again for its unfinished tasks.

The requested bundled commit/push is complete: `583a2b0`, pushed to `origin/main`.
It contains the accumulated safeguards, diagnostics, NASA sample inspections and plan status.
Precommit focused verification finished at 115 passing checks after a test-only subprocess
import-path repair; no full suite was rerun. Commit/push consent is spent for that operation.

The subsequent uncommitted continuation adds `analysis/tests/screen_long_route_windows.py`
and `docs/research-next-stage-20261006/long-route-window-screen.json`, with prose updates in
README, VALIDATION and PLAN_STATUS plus readiness metadata. It independently screens
120-minute windows every15minutes across the two documented normalized-track archives;
it does not require a passing75-minute anchor. All176windows are retained:130coverage failures,
one height failure,45motion-screened windows. Seven fixed-pattern controls passed observable
screening (sixAUHORD,oneORDLAX), none passed any contrast under either nominal wind candidate.
No eastbound control passed the heading screen. Runtime1.80s, zero new flight attempts.
Six existing motion/direction fixtures passed in0.45s. Scientific implementation is unchanged.
Fixed patterns and coarse starts are not exhaustive; no usable protocol is established.

The latest continuation adds `analysis/tests/screen_extended_route_controls.py`,
`docs/research-next-stage-20261006/extended-route-controls.json` and the human-readable
`EXTENDED_ROUTE_REVIEW.md` in that directory. It checks180/240-minute windows independently
of earlier anchors, with six fixed timing patterns per duration. The corrected run covers
277windows:250coverage failures,27screened,10preliminary passing controls (sixAUHORD,
fourORDLAX), allwestbound. No individual nominal contrast passes under either wind model;
no240-minute control passes preliminary geometry. Runtime2.6541s, zero flight attempts.
Six existing motion/direction fixtures passed in0.44s; all12pattern definitions satisfy
six-turn/spacing/edge rules. An invalid initial run is preserved in
`extended-route-controls-first-pass.json`:27covered windows hit schedule validation because
three initial patterns exceeded six turns;250coverage failures. It is not a science result.
The helper now validates all timing patterns before reading inputs. Changes remain uncommitted.

Latest timing continuation: `analysis/tests/screen_safe_turn_timings.py` scored88safe schedules
on11previously screen-passing windows (8perwindow), with up to512draws/window and caps96scores/
20seconds; neither global cap was reached. Runtime6.4081s. All rejected timings are preserved.
No pair passes across bothwind candidates. Physical wind alone gives10nominal partial schedules
(9ORDLAX,1AUHORD),16schedule/pair passes. `check_partial_timing_counterexamples.py` checked248exact
registered reference-TAS states in0.8625s:5passes disproved,11unresolved, never certified.
Corpus: `safe-turn-timing-screen.json`, `partial-timing-counterexamples.json`,
`TURN_TIMING_REVIEW.md` under `docs/research-next-stage-20261006/`.
52existing motion/direction/eligibility checks passed in1.43s;3new execution guards in0.38s.

`analysis/tests/check_observed_pair_envelope.py` and `observed-pair-envelope-plan.json` prepare
one full registered physical-wind envelope for actualORDLAX3600–10800s, turns5/15/30/40/90min,
comparison`sphere_still_vs_flat_still`. It has15,210SVDstates, estimate52.90s, cap120s,1thread,
science/input/helper/environment freezes and deadline checks. Default CLI only prepares;
`--run` requires separately approved compute. Scott authorized this one envelope on2026-10-07.
It completed all15,210states in29.7007s, under120s,1thread. Completed artifact:
`docs/research-next-stage-20261006/observed-pair-envelope-result.json`. Keep the frozen plan
unchanged because the result binds its hash. Target direct-pair retention0.3650996659622584,
threshold0.31224989991991997, margin0.05284976604233843, minimuminformation20.484201633970038.
Target passes both direct and global-cut calculations (cutretention0.3621652194879138).
Allstates have globalrank1. Direct rotationretention0.31461461894776643 passes narrowly,
but global-cut rotation0.3120686256034943 fails. Rotating-globe/disc direct0.14419675836858453
fails. Broad wind still fails nominally; physical wind assumptions need justification.
Independent reconstruction of the limiting epoch rotation reproduced target retention to1e-10;
all15,210state IDs are unique and plan/source/input/environment hashes match. No science source
changed; no extra tests were rerun for this data/docs-only continuation. Zero new flight attempts.
This envelope allowance is spent; no rerun or additional envelope/replay is authorized.
Next prepare a separately budgeted matched full-pipeline replay of this exact control under
three truths, combined wind/bias drift and both wind candidates, with axes actually recovered.
All continuation edits and the new result remain uncommitted; no fresh git consent.

Next: improve actual-route/control evidence under unchanged nuisance assumptions or obtain
a bounded budget for remaining full-envelope/full-pipeline work. NASA gyro decoding still
needs the exact physical payload schema; do not infer scale from fused navigation. No worker,
additional flight budget, empirical calibration, promotion or further git operation is authorized.
This section supersedes stale progress/authorization statements below.

## Analysis campaign handoff — 2026-10-05

### Current state and documentation — 2026-10-06

**Core-pipeline implementation (supersedes the source/pending-work statements below):**
The authorized pass implements shared aircraft-motion checks, diagnostics retention, observed
trajectory replay, a finite nuisance envelope and geometry-only turn optimizer, composable
wind/bias/noise/thermal adversaries, and opt-in direct pair-line profiles with separate calibration
and compatible pooling. No new campaign/search/calibration/validation is authorized or run.
Do not launch the prospective plan just because it has a manifest.

New scientific modules: `analysis/lll/maneuvers.py`, `trajectory.py`, `design_envelope.py`,
`design_geometry.py`, `profile_pairs.py`. New checks: `analysis/tests/test_core_pipeline.py`.
Preparation-only tool: `analysis/tests/prepare_core_pipeline.py`. Documented corpus:
`docs/core-pipeline-20261006/README.md`, `proposal.json`, `optimizer-estimates.json`,
and the ten explicitly generated specs in its `trajectories/` directory. The proposal records
the current implementation/config/policy/two-thread environment, source archives and input hashes.
Verification: 177 focused checks passed in 5.97s for that historical source hash:
`194a1c6ed0762dc8673adccee615d86d325cf44fc3079f0b251db4bbf46e629a`;
prospective manifest hash is `7a5c3a8f592eca621f9e0edca034fbd038c4815028752c3a45f9aa56319fc2aa`.
The user subsequently authorized committing and pushing this implementation together with the
prior local audit commit `bc00ec0`, then continuing development. Further campaign execution,
calibration and promotion still require separate authorization. New development edits after
that commit remain separate from this completed core-pipeline unit.
Five archived tracks have two replay modes each; two stay coverage-blocked. No actual-route
simulation has run. Original observations preserve unknown accuracy; dense observations and
the latent short-interval path are simulated assumptions. Long gaps and provider estimates
remain unsupported. The recorded ground path stays fixed under injected wind.

The maneuver guard rejects unsafe or unverified integrated IMU turns, excludes later uncertain
epochs and retains an integrity exclusion. Default analysis/three-model rules and the science
rank cutoff are otherwise preserved. Experimental `design_mode='envelope'` and
`pairwise_method='profile'` have new identities; old thresholds cannot be reused. Profiles use
their own convergence/bootstrap/prior gates and untruncated pair differences, while hardware,
orientation and selection checks still apply. Requested profile bootstrap must be nonlinear.
Observed replay cannot apply empirical policies in the harness or analyzer until calibrated
domain enforcement exists. Known axes in cheap design search do not certify reconstructed axes.

Next: review the prepared timing controls and finite envelope, obtain a separately bounded pilot
budget for new runtime/storage measurement, then real-route replay/search and complete-pipeline
comparisons. The ±10-minute single-turn controls violate the unchanged spacing rule and are
recorded as blocked. Unsafe timing controls must abstain, never become recommendations.
Physical wind/TAS fitting was subsequently implemented in the continuation below. Modeled
magnetic ambiguity, operational domain enforcement and a sharded runner remain deferred.
Keep the watchdog exclusions. No production promotion,
fresh calibration, git commit or push is authorized by this implementation request.

Historical source freezes and cost plans below remain historical; they are stale for new runs.
All completed allowances are exhausted. Use at most two total CPU threads; further calibration
requires final domain/source/environment approval, fresh calibration, then independent validation.

**Continuation and CI repair:** core work was committed as `a7efc53` and pushed with `bc00ec0`.
The user requested continued development and then reported failing Python CI. Run
37465056735 failed four existing end-to-end IMU-turn/crab checks; 321 checks passed. The new
bank-rate proxy differentiated a noisy GNSS estimate sample by sample, falsely marking clean
turns unresolved. It now uses the same 30-second physical window as the GNSS course estimate.
A new deterministic noise/maneuver regression covers this mechanism. Do not weaken the yaw,
bank, coverage or integrity thresholds to satisfy the old power assertions. Full recorded
campaigns remain historical; source changes invalidate their prospective freezes.

The opt-in physical wind/TAS candidate is integrated through free/fixed/global/pair profiles,
conditional speed constraints, bounded nonlinear bootstrap, geometry scoring and diagnostics.
`analysis/lll/wind_tas.py` freezes `wind-tas-1`; GPS supplies no independent aircraft heading
or airspeed observation. It requires `design_mode='envelope'`; requested bootstrap requires
`bootstrap_refit='nonlinear'`. Near-boundary fits abstain. The finite envelope checks both
3/6 dph noise levels explicitly. All defaults and the independent wind-truth generator remain.
Ten deterministic fixtures in `analysis/tests/test_wind_tas.py` passed in 8.80s, including an
independent simulator triangle and the public fit entry point with one deliberately inadequate
bootstrap replicate. The four previous CI failures passed locally in 98.09s. These are software
checks, not campaign/power/tail evidence.

Scott explicitly declined committing the CI repair and authorized the full Python suite.
The first run passed its analysis checks but stalled at the server's concurrent upload test
inside the sandbox. After a model change the agent mistakenly interpreted "back to normal"
as cancellation and interrupted that run; it did not produce a complete suite result.
Scott then authorized diagnosing and completing verification/documentation. A bounded
45-second server diagnostic isolated the stall in AnyIO's local async transport. Outside the
sandbox, all 13 server checks passed in 12.26s. Do not alter server code or weaken the race
test to accommodate sandbox behavior. Full-suite verification outside the sandbox completed:
**336 passed in 282.13 seconds**, one Starlette dependency deprecation warning, exit 0.
Future full-suite runs should use a process deadline and faulthandler diagnostics, with at
most two numerical threads, outside the sandbox for the async server tests.

Documented prospective corpus: `docs/wind-tas-development-20261006/README.md`, with its
preparation-only proposal and maneuver/optimizer estimate generated during this continuation.
The generated files are `proposal.json` and `optimizer-estimate.json`. They freeze current
scientific source `923281e6dc3765a2bdcea82f73bca860bde62f9c9f29c03d5df7405849066b99`
and two-thread environment `52cba9baed64e4096cc4b0bba352dbe3a3a366127a70ebcb4aa24fd8a91a8c98`.
Prospective manifest hash: `5d4e1cb9b44a5af92d3b69784f83ef77d5baa389be76139f85f827ad3403f2d8`.
The proposed FRA–JNB simulated-frequent-GPS lane uses shared fresh seeds 600700–600702,
three truths × wind/wind+bias_mixed/wind+bias_mixed+correlated+thermal × wind/wind_tas,
dynamic bias, axis/segment noise, measured forward uncertainty, envelope and pair profiles,
bootstrap zero: 27 shared recordings/54 evaluations. Turns 20/40/60 minutes pass the refreshed
two-minute-buffered assumed-path mask; no schedule search or real reconstruction ran.
Search upper bound is 5,571,423 SVD evaluations for beam 16, at most three turns and both fits.
New runtime/storage are unmeasured. The manifest was validated without running a flight;
there is no `campaign.json`. All additional execution allowances remain zero.
Older core proposals, timing masks and calibration plans remain historical and stale for this
source. Refresh rather than overwrite their evidence. Domain enforcement and sharding remain
outstanding; no campaign/search/calibration/promotion is authorized by this continuation.
Scott subsequently authorized their commit and push; the verified CI repair, wind candidate
and handoff were committed and pushed as `db28900`. No agents/delegation were used.

**Subsequent magnetic ambiguity implementation:** after that push Scott requested continued
work. The opt-in `magnetic_ambiguity='model_and_compare'` analyzer/harness path is implemented
with `analysis/lll/mount_yaw.py` and `analysis/tests/test_mount_yaw.py`. It requires envelope
design, direct pair profiles and nonlinear bootstrap when requested; empirical policies and
non-development harness runs are refused pending dual-path calibration. New documented corpus:
`docs/magnetic-ambiguity-development-20261006/README.md` (no campaign artifacts).

The watchdog only supplies flagged segment boundaries. Each flagged segment/mount epoch gets
bounded yaw-offset/rate parameters under provisional `mount-yaw-1`; positive IMU yaw is about
up, opposite to fuselage crab about down. First flagged boundary bins are excluded because the
instantaneous step's gyro impulse is not modeled. Later offsets persist within the same epoch.
The finite envelope checks individual +/-3-sigma yaw/rate states, not all combinations.
Fits include mount bounds, analytic derivatives and widened-prior checks. Primary and pair
boundaries cause abstention. The analyzer reruns the original exclusion path with its own
preprocessing/forward estimate/WMM sensitivity; both scientific gates, endpoint decisions and
estimates must agree. Unusable exclusion data cannot be rescued by the retained fit. Integrity,
selection and pair-specific rank/uncertainty gates remain. Default exclusion behavior is preserved.

Verification: **119 focused checks passed in 15.90s** across mount-yaw, eligibility, core pipeline,
wind/TAS, research candidates and hardening. This includes independent passive rotations, zero
and +/-3-degree/hour yaw controls, bounded/nested profiles, malformed-decision abstention and
encoded recording checks that rerun the original control. No full-suite rerun, flight campaign,
optimizer search, calibration or validation occurred after `db28900`; the earlier 336-test full
suite applies to that committed source. Operational domain enforcement and sharding remain.
All prospective manifests below are historical/stale after this source/policy extension, including
the 54-evaluation wind comparison. Refreeze before executing an approved pilot. No additional
compute allowance exists. The new magnetic work is uncommitted; further git operations require
fresh consent. Current scientific hash and focused verification are in `readiness.json`.

**Subsequent observable-domain implementation:** the continued pass implements
`analysis/lll/flight_domain.py` and `analysis/tests/test_flight_domain.py`. New documented corpus:
`docs/flight-domain-development-20261006/README.md`. `observable-flight-domain-1` requires
explicit finite bounds on every supported retained-bin property, a fixed mount-epoch timing
envelope and exactly one acquisition source. The analyzer derives that source and refuses
overrides. Geometry reads no fitted gyro coefficients or truth labels. Membership is recomputed
by the shared primary/pair gate; missing, inconsistent or outside bindings abstain. The fitter
always retains observable diagnostics. Empirical artifacts supply their frozen domain; explicit,
primary and pair domains must agree. Bare threshold dictionaries cannot bypass the binding.

New primary `empirical-decision-5` and flight `pairwise-empirical-3` policies include `domain_id`
in operational keys. The harness canonicalizes `--flight-domain` content into settings and the
manifest, and requires it for new flight calibration/validation preparation. Record validation
checks the freeze, including outside-domain records; duplicate seeds cannot migrate between
domain/rank strata. Independent validation requires the same descriptor. Profile campaign cells
are parsed from diagnostic metadata instead of confusing comparison/method keys with global rank.
Historical unscoped artifacts remain readable for offline research and now abstain on empirical
flight application. Default diagnostic analysis remains available. Domain implementation is
included in the scientific source hash. Public-track empirical analysis and magnetic dual-path
empirical decisions remain refused. A flight domain cannot transfer to summary pooling.

Verification: **156 focused checks passed in 29.71s** across domain, eligibility, hardening,
mount yaw, core pipeline, research candidates, wind/TAS and identifiable design. Subsequently,
**70 domain/eligibility/hardening checks passed in 1.14s** after source-freeze inclusion, including
a regression proving domain-module changes alter the implementation hash. Current scientific
hash is `3e6978e29d2c2041c2d82246b906c9491e2beb0ceb8fa3e93b11c7afaecb7c24`;
the two-thread environment hash remains `52cba9baed64e4096cc4b0bba352dbe3a3a366127a70ebcb4aa24fd8a91a8c98`.
Final verification/source identity are recorded in readiness. No full-suite rerun, optimizer search,
flight campaign, calibration or validation occurred. No usable domain, thresholds or promotion
was approved. Earlier prospective manifests remain stale, all additional attempts remain zero.
The magnetic and domain work remain uncommitted; git operations require fresh consent.
Sharded execution remains the next engineering stage. Scientific next steps still need a
separately bounded pilot/search budget, domain/source/environment review, fresh calibration,
frozen thresholds and independent validation. No subagents were used.

**Subsequent sharded-runner implementation:** continued work implements
`analysis/lll/campaign_shards.py`, `analysis/tests/sharded_campaign.py` and
`analysis/tests/test_campaign_shards.py`. New documented corpus:
`docs/sharded-campaigns-20261006/README.md` (documentation only; no executed campaign).
The existing research CLI's `--write-sharded-plan` freezes exact candidate jobs into the
scientific manifest, plus deterministic implicit task axes, shard assignment and decision-file
contents. Preparation runs no flights and grants no budget. Runtime requires an explicit
`--attempt-limit`, a total prefix including all previously started attempts. New local workers
are capped at two processes, each with BLAS/OpenMP threads **1 before numerical imports**.
The old two-thread scientific environment cannot be reused for these workers; refreeze.

Every shard fsyncs hash-chained start/completion events and its new directory entry. Completed
successes/failures are never repeated. Lost started attempts become infrastructure failures on
resume, with no fabricated statistics and unknown runtime (`elapsed_s=null`). Only incomplete
final bytes may be repaired, after byte-for-byte recovery archival; complete corruption, gaps,
duplicates, changed provenance/source/environment and wrong-shard records are refused. Scientific
source is checked before and after each task. The adapter calls existing `realize`/`flight_run`;
RNG streams and eligibility are preserved. Existing pool/replay/magnetic empirical restrictions
remain. A partial merged export is refused as calibration/validation evidence.

The coordinator checks orphaned workers before spawning replacements and uses locks to exclude
duplicate writers/live merges. An explicitly requested `--detach` launch uses a separate process
session, persists PID/command/logs and waits for ready child status. In Codex it still needs an
escalated launch to survive sandbox exit; no background process was launched during this pass.
Normal SIGINT/SIGTERM cleans up coordinator children. SIGKILL can leave bounded children working;
check status/PIDs/locks before resuming. Merging streams records in task order into an atomic
campaign file, preserves failures and reports coverage/unknown runtimes. Its `elapsed_s` is the
sum of known per-attempt times, not coordinator wall time or a complete cost estimate.

**94 focused checks passed in 6.90s**, covering the new runner, domain, eligibility, hardening
and existing development-worker recovery. Two actual OS processes wrote only fixture records;
another fresh interpreter verified one-thread setup before scientific imports. No synthetic
flight, search, calibration or validation ran; no full-suite rerun or measured campaign speedup.
Current source hash: `d5d63a6eec604ac2ba02cb39648767a914841f3c05bb8790eeb1ef442f95cb42`.
Readiness records this freeze and verification. All extra attempt allowances remain zero.
All prospective manifests remain stale, including the 54-evaluation wind comparison. The
magnetic, domain and runner changes remain uncommitted; further git operations need fresh consent.

The review implementation/engineering stages are now present. Scientific next work remains:
review finite nuisance/domain assumptions, approve a bounded runtime/storage pilot and route
search/replay, choose a usable domain, refreeze final source/configuration/policy/environment,
then separately authorized fresh calibration, frozen thresholds and independent validation.
Real IMU bench qualification, operational public-GPS recovery and real pooled-domain calibration
remain separate. Do not interpret implemented software as demonstrated model separation.

**Latest authorization — initial airline pilot:** after the explicit initial-three budget
question, Scott replied “continue.” This authorizes exactly the first **3 matched evaluations**
of `docs/airline-pilot-preparation-20261006/plan.json`, with two single-thread workers.
The approved prefix is now **complete and exhausted**, with three preprocessing failures;
no worker is active and no additional attempts are authorized. Output corpus:
`docs/airline-pilot-preparation-20261006/run/` (plan, launch/status, coordinator
and shard logs, locked hash-chained journals, merge status and partial campaign export).
Check its status before any resume; use the same plan and total `--attempt-limit 3`, counting
all started attempts, including failures. Never retry an interrupted started attempt or launch
a duplicate. This supersedes zero-allowance statements below only for this three-attempt prefix.
The remaining 15 proposed cases, optimizer search, calibration, validation and git operations
are not authorized. Runtime is unmeasured; no wall-time ceiling was promised. Keep scientific
source unchanged while workers run. Coordinator PID 3610970 finished with `budget_complete`.
Wind/exclude failed for unavailable measured forward uncertainty; wind-TAS/exclude and
wind-TAS/model-and-compare failed for missing three-axis forward reference. All fail before
science fitting, envelopes or pair profiles. Saved-data reconstruction found identical
forward gain 0.0487347 and R² 0.0122685, below existing 0.1/0.05 requirements; bank energy
0.657473, no unresolved orientation epoch, 57 retained bins. Attempt times 8.1355/8.2483/6.3878s
sum to 22.7715s; these failed-preprocessing costs cannot price successful fits. Run storage
snapshot: 14,958,617 bytes. Do not resume completed tasks, substitute known simulator axes,
weaken the gate or run the remaining 15 cases. Diagnose assumed trajectory roll versus the
GNSS bank proxy using saved data before another newly authorized replay. New documented
audit helper `analysis/tests/audit_airline_pilot.py` writes the corpus artifact
`docs/airline-pilot-preparation-20261006/processing-review.json`; it runs no synthesis,
science fit, SVD or search. README/validation/readiness now record the blocked comparison.

**Latest authorization — fresh matched pilot:** the explicit question authorized only the
initial three fresh evaluations; Scott answered “keep going.” This approves exactly prefix
indices 0–2 of `docs/matched-airline-pilot-20261006/plan.json`, fresh seed 600901, two
single-thread workers maximum. The other 15 cases, calibration, validation, optimizer search
and git operations remain unapproved. Original failed seed-600900 attempts are not retried.
Execution corpus: `docs/matched-airline-pilot-20261006/run/`, including its bound plan,
launch/status, coordinator/shard logs, locked hash-chained journals, partial campaign export
and merge status. Check status before any resume; total `--attempt-limit 3` includes every
started attempt and preserves successes/failures without reruns. Do not change scientific
source while workers run. No successful-fit runtime estimate or wall-time cap was promised.
This three-attempt authorization supersedes zero-budget statements below only for this prefix.
Record all results and update docs/readiness before proposing further spending.

**Completed fresh matched pilot — supersedes preparation/running statements below:** prefix
0–2 is complete and exhausted; `run/status.json` is `budget_complete`, both shards complete,
no active worker, zero additional authorized attempts. All three fits converged with no
analysis failures, but zero primary or pairwise eligibility. Retained cruise 57 minutes,
heading span 15.465°, insufficient heading diversity; all worst design contrasts fail.
Free model-test ranks 0/1/1; worst design rank 0 for each. The matched reference passed with
gain 0.785061, R² 0.749727, sigma 0.685600°. No watchdog boundaries were flagged; retained/
excluded coefficients were identical, but agreement was unavailable due to failed contrasts.
Do not report mount movement or numerical disagreement from that agreement flag.

Attempt runtimes 6.260351/72.624785/123.957378 seconds, total 202.842514; observed wall
131.358896 seconds (launch UTC to final status filesystem mtime), storage snapshot 39,234,307
bytes. No bootstrap, thresholds or independent validation. One matched generating condition
is not three independent null draws. Original 15 remaining tasks must not run without a new
budget, and this failed window should not be the next expensive comparison.

New documented reports `docs/matched-airline-pilot-20261006/results-review.json` and
`route-screening.json`; report-only helpers `analysis/tests/review_matched_pilot.py` and
`review_route_geometry.py`. The cheap five-window screen uses the shared heading-duration
rule on explicitly assumed C2 paths before IMU exclusions; only AUH–ORD passes optimistically.
ORD–AUH has wide span but distant headings are too brief. This is no guarantee of acceptance
or actual flight motion. Next: route/window and turn-timing preflight with existing observable
gates, then separately budget any fit/design-envelope evaluation. Scientific source remains
`82c882d2abf351cb0feb0e8efa237702d1deeccd475d682960419677bf479412`.
No full-suite rerun or git operation this turn; later extensions remain uncommitted.

**Latest geometry preflight and prepared extended pilot:** continuation ran only cheap
assumed-route screens, no additional flight, fit, SVD or optimizer-envelope evaluation.
New documented helpers `analysis/tests/preflight_route_turns.py`,
`preflight_route_windows.py`, `preflight_extended_window.py`,
`prepare_extended_airline_pilot.py` and four controls in `test_route_turn_preflight.py`.
Controls passed (4, 0.29s); no full-suite rerun. Reports in the matched-pilot corpus:
`turn-preflight.json`, `turn-motion-review.json`, `window-preflight.json`,
`extended-window-preflight.json`. Read only the two explicit documented normalized archives,
not original home files or unfamiliar paths. Source remains `82c882d2...`.

The analytic motion screen rejects all five originally selected 75-minute windows. Across
all seven tracks, 192 coverage-qualified overlapping windows, one missing-height failure,
73 with >=60 no-turn screened minutes, 9,640 safe three-turn schedules and no passing window.
Only AUH–ORD elapsed 41,400–45,900 passes both duration and heading before turns, with exactly
60 screened minutes. Course/vertical/bank-rate conditions contribute; omitting bank rate
alone does not restore a viable 75-minute route. Analytic screen differs from full preprocessing;
never infer actual aircraft attitude or unusable real flights from interpolated derivatives.

Checked 21 overlapping 90/105/120-minute extensions containing that development anchor;
19 have passing schedules. Selected new candidate: Etihad 9 AUH–ORD, elapsed 40,200–47,400
seconds (120 minutes), observed interval coverage 0.995833, turns **25/50/85 minutes**,
91 screened cruise minutes, epoch totals 23/20/23/25, heading-duration margin 420 seconds.
No acceptance rule changed; forward reference and nuisance separation remain untested.

New documented corpus `docs/extended-airline-pilot-20261006/`: README.md, plan.json,
preparation-review.json. Fresh seed600902, source82c882d2..., one-thread environment
20ef3938..., plan `d2337e3a4bbe4da89f9b446d9b49c7ca0f19f13d94172a0bb81861696549eae0`,
trajectory `0dcd534e05f0621361898f0c1f6a98663aaa76635d07f9059dcb4e5719e7bf16`.
Full proposal18 matched evaluations, initial3 proposed, **zero authorized or run**. Do not
transfer the spent older prefix or its remaining15 tasks to this plan. Fresh initial prefix
would compare wind/exclude, wind-TAS/exclude and wind-TAS/model-and-compare on shared rotating
truth with wind+mixed bias, no bootstrap. Two single-thread workers maximum. Runtime for
this longer route unmeasured; original prefix was ~131 wall/~203 attempt-seconds. Prepare
and review before requesting a new explicit three-attempt allowance. No calibration,
validation, promotion, git operation or extra flight is authorized by this preflight.

**Latest authorization — extended airline pilot:** the explicit request for its initial
three evaluations was answered “keep going.” This authorizes exactly prefix indices 0–2
of `docs/extended-airline-pilot-20261006/plan.json`, fresh seed600902, at most two single-thread
workers. The older plans stay complete and spent; the other15 new-plan cases, calibration,
validation, promotion and git operations are unapproved. Execution corpus is
`docs/extended-airline-pilot-20261006/run/`, with the runner's documented bound plan,
launch/status, coordinator/shard logs/locks, hash-chained journals, diagnostics and partial
campaign export. Check status before resume; never start a duplicate or retry completed
failures. `--attempt-limit 3` is the total budget across resumes, not three additional attempts.
Do not change scientific source/environment during execution. This specific authorization
supersedes the prepared/zero-authorization statements above only for this three-task prefix.
Record results and update docs/readiness before considering additional spending.

**Extended airline pilot complete — supersedes running/prepared statements:** prefix0–2
is complete and spent, `run/status.json` is `budget_complete`, both shards complete, no active
worker, zero additional authorized attempts. Three converged fits, no analysis failures;
actual preprocessing retains 97 cruise minutes with adequate heading diversity (51.095929°
span), four epochs, maximum gap520s. The preliminary screen was91 minutes; it is no bound
on the different full preprocessing. Forward reference passes: gain0.979168, R²0.925423,
sigma2.190851° (112 covariance support windows, coverage unvalidated).

All free model-test/design ranks0, every primary/pair contrast fails. Physical untruncated
retained fractions0.174659/0.077359/0.196523 remain below0.3122499; changing the SVD cutoff
alone does not fix retention. No magnetic flags, identical retained/excluded coefficients,
zero shifts; agreement unavailable due to nonidentifiability, not numerical disagreement.
Physical speed chi-square207.895981, relative margin0.320117, no boundary flag.

Runtimes24.285724/147.287569/256.638571 seconds, sum428.211864, observed wall282.394589
seconds (launch UTC to final status file mtime), storage49,961,789 bytes. New documented
`docs/extended-airline-pilot-20261006/results-review.json`, generated by the existing report
helper without new fits. Campaign SHA256270b5dc62022021bd8fc10d790100bdd48a723527c100f5e646dfee5ec6944bf.
Source remains82c882d2..., plan d2337e3a..., one-thread environment20ef3938.... Initial3 use
one shared generating condition, zero bootstrap; no threshold, coverage/error claim or model
winner. Previous75-minute pilot has a different seed/route and is not a duration-only control.
Remaining15 cases are unrun/unapproved. Next: diagnose nuisance-direction and forward-axis
uncertainty contributions from preserved diagnostics before a separately budgeted route/schedule
comparison. No additional attempt, source change, calibration, validation or git authorization.
Docs/readiness and artifact hashes record this completion. No full-suite rerun this turn.

**Latest saved nuisance diagnosis and design-tool repair — supersedes current-source82:**
No new flight, refit, bootstrap, calibration or validation ran. Helpers
`analysis/tests/audit_nuisance_directions.py` and `audit_model_signal.py` read only the known
extended-pilot arrays. New reports `nuisance-direction-review.json` and `model-signal-review.json`,
plus `DIAGNOSTIC_REVIEW.md` in that corpus. Before the repair, they use the pilot's exact82c882d2
freeze: reconstruct stored Jacobians with the recorded mount-transformed forward tangent;
do not substitute cross(up,forward) per bin. All-orders attribution across nuisance subsets
reproduces recorded limiting retention.400 checks in0.286s; third saved tangent identical.
Seven independent diagnostic controls passed in0.19s (`test_nuisance_direction_audit.py`).

Bias drift dominates most losses already at nominal conditions. Physical nominal rotating-
anchor fractions0.185994/0.107847/0.199518; omit drift only diagnostically0.5262/0.2895/0.6058,
omit wind0.1886/0.1107/0.2011. No single family omission fixes every contrast; do not delete
real drift or tighten uncertainty to force acceptance. Unpenalized local spans admit arbitrary
amplitudes; this does not show actual hardware drift or prove nonlinear bounded compensation.
This westbound route also weakens the raw rotating-vs-disc signal: north Earth10.6614°/h plus
transport−6.6632°/h, net3.9983°/h. Vertical contrast−13.3791°/h varies only0.1379°/h; tray yaw
turns leave it unmodulated. Bias level alone retention0.30966 below0.31225. Eastbound/other
geometry and better modulation deserve a cheap screen, not another blind pilot.

`analysis/tests/screen_turn_followup.py` checked six fixed patterns on unchanged assumed
trajectory and nuisance models, no full-envelope search. An SVD failure exposed an analytic
tool bug: `design_geometry.geometry_problem` unwraps across NaN gaps, poisoning later courses.
Fixed **only** `analysis/lll/design_geometry.py` to unwrap finite runs separately; no bridging
or exclusion weakening. New `test_design_geometry_gaps.py`:2 controls0.21s. Four existing
coverage/envelope/optimizer controls pass0.84s. Completed full-pipeline outcomes unaffected.

Current source is **a7cc619428f8a24f96e3ab77e5d99f1c5b1b92639b2f6c6e3cfed937176cf44f**.
Completed campaigns and saved-array audits retain82c882d2; read their preserved reports rather
than loosening source guards to recompute under another freeze. New `turn-followup-screen.json`
records a7cc6194 current source and82c882d2 input-plan source. Of six patterns, original3 and
distributed6 (10/30/50/70/90/110) pass buffered motion; tested10-minute clusters fail at45/75/95.
Distributed6 keeps85 analytic minutes, improves physical worst nominal fractions to
0.27148/0.12458/0.30510, still no all-contrast pass. Nominal geometry is no acceptance guarantee.
All old prospective execution plans are stale; refreeze before a newly authorized run. Next:
screen directionally different route/modulation controls while keeping nuisance space; only
promising controls warrant budgeted full-envelope and full-pipeline work. All additional
attempt allowances remain0, no active workers, no full-suite rerun or git authorization.

**Latest shape discriminator and NASA source review — supersedes current source a7cc6194:**
Scott explicitly requested globe-versus-non-globe evidence and continuation. Implemented
`globe-disc-pair-rule-1` in `lll.pairwise.shape_evidence`: globe preference requires at least
one eligible, consistent globe/disc pair retaining its globe and rejecting disc; disc requires
both pairs retaining disc/rejecting globe; opposing preferences abstain. Rotation-only pair
is irrelevant. Scope is the two implemented globes versus the specified stationary disc,
not every non-globe hypothesis. Never treat neither/both rejected endpoints as a preference.
Candidate fits, final flagged analysis, flight/pool research records, pool output, research
summaries and readable HTML carry the experimental shape result. Pair eligibility, domain,
bootstrap, prior and magnetic-path gates remain intact. `pairwise_thresholds_calibrated` only
describes inputs; composite `error_rate_validated`/`validated_for_primary_claims` remain false.
Disc-null union can accumulate endpoint errors; current endpoint calibration/assessment is
not composite validation. Preregister a shape error budget and validate under all three truths.

Geometry optimizer `--objective globe-disc` requires both untruncated shape contrasts over
the unchanged nuisance envelope, without rotation separation/global rank. Default three-model
objective remains. Single `--comparison` is separate and cannot combine with shape objective.
No new optimizer search, envelope sweep, simulated flight or empirical refit ran this pass;
nonlinear solves were confined to small deterministic software fixtures.
`analysis/tests/review_shape_evidence.py` reads only the two preserved development archives,
retaining old eligibility/endpoint decisions, and writes
`docs/research-next-stage-20261006/shape-review.json`. Correct/incorrect/abstain counts:
889/0/111 and900/0/100; 9/12 extra preferences without a recorded three-model winner.
Historical observable-coordinate synthetic evidence is not current airline/direct-profile
evidence or calibration. Original files and freezes were preserved.

46 focused checks passed across1.47s+0.69s: exhaustive shape outcomes, stale/excluded evidence,
calibrated-input labeling, informative-unit pooling, rank0 profile gate integration,
shape envelope objective/worst nuisance candidate, research failure denominators, readable
report, existing pair/optimizer controls and candidate fit/separate calibration integration.
No full suite ran. Current scientific hash:
**1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500**.
All prospective plans remain stale; all additional attempt budgets remain0. No git operation.

Scott supplied `https://data.nasa.gov/dataset/icebridge-lvis-l0-raw-ranges-v001` and asked whether
it is airborne and useful. NASA/NSIDC metadata and the eight-page Level0 guide confirm airborne
LVIS raw IMU (`applanix`/`gyro`), GPS, camera and `planedata` streams,2009-2017. Formats vary
binary/text and instrument; sample rate, axes, timing, calibration and processing unresolved.
Raw gyro is promising for a separate empirical discrimination study; navigation-derived
attitude may already encode Earth rotation/curvature. Do not import corrected attitude as
independent gyro evidence or imply WT901 validation. `AIRBORNE_DATA.md` in the next-stage corpus
records primary-source links and small-sample inspection order. NSIDC says Earthdata login
required. No measurement downloads, credential inspection, decoder or empirical test occurred.
Next inspect a small documented raw sample/schema if available, alongside nominal route/turn
screens with shape and rotation objectives; expensive studies still need their own budget.

**Authorized commit/push and precommit verification — current continuation:**
The user requested "commit and push then keep going". Bundle the accumulated related review,
analysis development, pilot evidence and airborne inspection/documentation as one commit.
All three documented pilot run/status files reportbudget_complete; no active campaign files
are being included. Transient empty runlock files are excluded from staging, no files deleted.
Focused nine-module precommit run:114 passed,1 subprocess-fixture import failure in13.94s.
Child imported test_campaign_shards without a test-source path, depending on inherited
PYTHONPATH. Fix test-only launcher to supply explicit test/analysis paths in the child;
failed actual two-process merge fixture now passes1.47s. Scientific sourcehash unchanged.
No fullsuite or new simulations run. Readiness records focused evidence and repaired testhash.
This request authorizes this one commit/push; later changes require fresh git consent.

**Earlier continuation / original plan status:**
The user asked "what next? keep going?" and "there was also the plan. anything left in that?"
Review code/engineering items are present; scientific route/domain proof, physical wind/TAS
assumption justification, dual-magnetic-path calibration, pair/pool/composite-shape error budgets,
hardware qualification, fresh calibration and independent validation remain. New documented
`docs/research-next-stage-20261006/PLAN_STATUS.md` maps the blind review's8items plus sharding
to implementation/evidence and orders remaining work. Do not conflate completed code with
demonstrated identifiability or a validated protocol. Additionalflightbudget remains0.
New offline `analysis/tests/check_direction_counterexamples.py` performs at most30SVDchecks
on the counterfactual reversed120minpath/sixsafe turns using exact existing registered
physical-wind/TAS-reference states; no synthesis/no nonlinearfit. Recorded report
`direction-envelope-counterexample.json`:30states,0.100963s, no failure found, minimumshape
retentions0.403480/0.431011 versus0.312250. Windzero/someindividualdrifts, offsets0/±15deg;
cap ends partway through one state group. Not completeenvelope; omittedwindcorners/TASlevels/
epoch/noisestates untested. Broadwind alreadyfailsnominal; reversal notobservedflight.
Result is bounded/inconclusive, no robustpass/power/calibration or protocol recommendation.
Publicformat research still finds no exactphysicalIMU8definition. FORMAT_FOLLOWUP.md records
manufacturer support URL/email and documented WaypointIMRexport schema, with converter
compatibility unverified; nopurchase/install/convert, no inventedscale. NovAteltypenumber8
is not evidence identifying/scaling ApplanixIMU8. CaltecholdLV4ICD publiccurl failedTLSissuer
verification after authorized outside-sandbox retry; no insecure TLS bypass. No credentials
or messages inspected/sent. Exactdocumentation request remains unsent; external contact needs
explicit instruction. Source scientifichash unchanged1bf8; newhelper/report/docs hashes in
readiness. No heavytests/newflights/workerlaunch/gitoperation. Next cheap observedgeometry
screens are independent of NASAformat; bound costs and ask before fullenvelope/fullpipeline.

**Earlier ILVIS0 time-tagged IMU sample:**
The user supplied `~/Downloads/ILVIS0_gyro_54935_atm_applanix_14Apr09.013` (13,086,748 bytes,
SHA25618c48772bcd7e83566f2301ae3689d691c1675dfc2e60c0650b6e0017b764096). Only this explicit
path was read. Offline `analysis/tests/inspect_ilvis0_sample.py` verifies all143,471 complete
outer frames/checksums (sum of little-endian16bit words includes terminator; no resync/repair).
132,444 Group4 packets at~200Hz, span662.2256497321068s, no gaps>7.5ms. Headerstatus0,
IMUtype8/ratecode2, version AV-510 VER5 firmware04.60-Oct21/08 ICD15.00 IMU8 PGPS16.
The public NASA-hosted2014 V6 ICD matches containers but is not exact firmware documentation;
24byte IMU payload stays opaque. No guesses of physical scale, axes, rate/increment convention,
calibration, gyro Earth-rate subtraction or proprietary status meanings. Group10002 absent.
662 Group1 fused navigation records; never substitute its attitude/rates as independent gyro.
5934 Group10001 frames reconstruct primary GPS before parsing:660 valid GGA,660 VTG,660 ZDA,
all sentencechecksums pass, fixquality1, date2009-04-14. Reassembly matters:10GGA markers split
across containers. Timebyte2 = UTCtime1/POSsincepowerontime2 in compatible ICD. Absolute
sensor/GNSS alignment/latency and mounting/lever arms unverified. Navtrajectory Greenland
southbound79.72N→78.86N; altitude~6.9→7.5km, rollmin−17.5deg, climb/maneuvers, not qualified
levelcruise. No physicalgyrodecode, primarypipelineimport, empiricaldecision or WT901 validation.
Documented corpus `docs/research-next-stage-20261006/airborne-sample-ilvis0/`: originalfilename.gz
(lossless), imu-packets.csv.gz (time/header/opaquehex), navigation.csv (fused),
primary-gps-stream.bin.gz (reconstructed), gps-sentences.txt, gps-fixes.csv, inspection.json,
README.md. Input/helper/artifacthashes inreadiness. Two focused checks pass0.02s: fullframe
checksum inclend, truncation/damage rejection, receiverchecksums/reassembly/signedcoordinates.
Next obtain IMU8payloadformat or uncorrectedphysicalexport withunits/axes/timing/corrections;
AIRBORNE_DATA includes a precise documentation-request draft, not sent. No more logs needed
until format known. No credentials/authused, message sent, newflight, fullsuite or gitoperation.
Scientific sourcehash unchanged1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500.
Additionalcampaignbudget0. Don't claim units or independence from plausible-looking counts.

**Earlier supplied IPUTI0 navigation sample:**
The user supplied exactly five files in `~/Downloads`: `ASB_JKB0a_GL0017a_AVNcp1.bxds`,
`ASB_JKB0a_GL0017a_AVNcp1.ct`, `AN09.IPUTI0.AVNcp1.bxds.format`,
`AN09.IPUTI0.AVNcp2.bxds.format`, and `AN09.IPUTI0.ct.format`. Only those explicit paths were
read; no credential inspection or directory enumeration. Originals are now documented and
preserved in `docs/research-next-stage-20261006/airborne-sample-iputi0/inputs/` with hashes.
Offline `analysis/tests/inspect_iputi0_sample.py` decodes status3500 and navigation3501 only;
both occur in the AVNcp1-named binary. Formats specify fixed-point position/velocity/attitude,
no independent raw gyro rates/increments. No Earth-model decision, synthetic flight or
main-pipeline import was run. Navigation-derived angular rates would not be independent.
1,527 valid packets of each kind; one false navigation candidate at10800 fails checksum,
valid frames begin11bytes later. All11unframed bytes preserved; cause unknown, no repair.
Clock relative span1525.99469s, approximately1Hz; wallclock2010-01-01 07:31:49.09–07:57:14.93
is approximate with timezone unverified. Binary64bit timetag representation/epoch/alignment
unresolved; exact bytes retained in exploratory navigation.csv, no guessed times. Horizontal
speed69.51–93.69m/s. Status flag meanings unknown. Byte order/additive checksum inferred from
sample, not verified manufacturer specification. No corrections/mount/calibration established.
Three focused tests pass0.02s: resync inside rejected candidate, signed units/truncation,
relative clock units/nonmonotonic rejection. SampleREADME/AIRBORNE_DATA/mainREADME/technical
validation/readiness updated. Scientific hash unchanged; new helper/sample hashes inreadiness.
Earthdata account created, toolauth unverified. Next inspect independent ILVIS0 Applanix gyro
sample/schema (directlink in AIRBORNE_DATA), or documented distinct raw-sensor stream.
These IPUTI0 layouts support aircraft-motion study after timing/processing checks, not a raw
gyro discriminator. No new campaign/fullsuite/git authorization; remainingflightbudget0.

**Earlier NASA access and nominal direction screen:**
The user said keep going, supplied CMRconceptC1386246599-NSIDCV0, and now confirms **Earthdata
account created**. Browser download of the cataloged ~12.5 MB ATM gyro sample is the next step;
AIRBORNE_DATA.md contains its direct link and Earthdata Search fallback. Tool authentication
and successful measurement access remain unverified; no credentials, tool login or bulk
download is authorized or performed. Source measurement access awaits a documented sample. Do not inspect
home credential files or silently obtain/use stored authentication.

NASA's public catalog resolves ILVIS0 currentcollectionC3162704221-NSIDC_CPRD, DOI
10.5067/E6JPQ3QNW77R.10 filename gyro candidates in first20 records;5 remote GPS filename
candidates for2009-04-14. They include distinct ATM/LVIS instruments, day-wide metadata times;
same-day files are not proven same-flight overlap. Exact modest sample lead:
`ILVIS0_gyro_54935_atm_applanix_14Apr09.013` (~12.48reportedMB), or LVIS
`ILVIS0_gyro_54935_lvis_applanix_POSAV.031`. A64KB range probe returned302 to
urs.earthdata.nasa.gov,0 measurement bytes. No data payload was inspected.
The alternative record is **different IPUTI0**, DOI10.5067/7K31MCH5XXZA, Systron Donner
MMQ-G onBT-67, Antarctica2009–2010, ASCIIposition/velocity/pitch/roll/heading metadata.
Its listed directory also returned302 toEarthdata login. No filenames or gyro columns known.
No accessible user guide was obtained. Do not classify orientation alone as independent raw
gyro evidence. Applanix2014 V6manual/ICD is a possibleformat lead only; groups4/10002 payload
details unpublished,2009hardware applicability unverified. Never guess scaling or use group1
navigation angular rates as raw gyro. No export-control/legal assessment is needed; obtain
documented sensor output/schema or an understood export if available.

New next-stage documented artifacts: `airborne-catalog-review.json`; four public compressed
metadata originals in `airborne-metadata/`: `ilvis0-collections.json.gz`, `ilvis0-granules.json.gz`,
`ilvis0-gps-granules.json.gz`, `iputi0-collection.json.gz`. No authentication headers/bodies/
redirect parameters copied. Offline `analysis/tests/review_airborne_sources.py` inventories
these explicit files, sourcequeries/hashes, identities and recorded access checks; it does not
retry network probes or decode measurements. AIRBORNE_DATA.md has minimal download/resume steps.
Networkmetadata fetches required outside-sandbox escalation; none affected science source.

`analysis/tests/screen_route_directions.py` completed21 fixed controls on5 prepared75-minute
C2paths, extended120-minuteAUHORD and counterfactual reverse.12 safe patterns,24 candidate
evaluations with2 no-qualifying-bin failures,0.542s. No envelope search or new flight.
Report `docs/research-next-stage-20261006/route-direction-screen.json` and DIRECTION_REVIEW.md.
Reversedpath six turns10/30/50/70/90/110 gives85 analyticmin, adequate headings, physical
wind shapepre-cutoff fractions0.415376/0.436039, rotation0.298360 (fails). Originalsamepattern
shape0.124577/0.305099. Broadwind reversedshape0.253845/0.293767 stillfails; no pattern passes
both shapecontrasts underboth candidates. SEA–KEF physicalshape nominalpass0.333473/0.415521
is ineligible55min and inadequateheadings. Nominal3anchors/zero nuisance/TAS250/noise6;
no fullenvelope, recoveredaxes, bootstrap/power. Reversal is not an observedreturnflight.
Two independent reverse-motion controls pass0.39s (positions/support/speed, signed
derivatives/course, nonmutation/involution, irregularsampling). Scientific source remains
1bf8f7c0120fa84504d98c377db61807cacf9f2db6fdcec20f814b9f4a4d8500. All newhelper/input hashes
are inreadiness; no fullsuite or git operations. Additionalflight budgets remain0.
Next resumeNASA sample/schema after the user supplies the downloaded file's exact path; cheap real-window/safe-turn shape screens
can continue without it. Do not pickphysicalwind solely to obtain a pass. Broadwind still
limits the checked geometry; only justified candidates warrant separately budgeted fullenvelope
and fullpipeline studies, followed by freshfreeze/calibration/independentvalidation.

**Supplied video reference:** `https://www.youtube.com/watch?v=Yw-oXwjoJ3A`, reported roughly
4 fps and horizontal field of view ~4.75°, height smaller. The browser fetch failed; no frames
downloaded or measured. Camera was on a tripod on the tray, reported as stable as practical;
mount configuration is known but tray/tripod rigidity is unmeasured. At full uncropped width,
a 1% horizontal shift is approximately
0.0475° scene angle. Before deriving aircraft attitude/rates, establish mounting, cropping,
scene geometry and whether 4 fps describes capture or playback/time-lapse. Record this as
supplied metadata, not measured motion or a new synthetic nuisance amplitude. Reference is
documented in the matched-pilot README; no new flight budget or git authorization follows.

**Latest matched-reference integration:** `analysis/lll/forward_reference.py` implements
`matched-forward-1`: common 30s Hann filtering, joint observed GPS/IMU score covariance with
run-separated 60s Bartlett HAC, frequent GPS (median interval ≤2s), four full covariance-duration
windows and the existing energy/gain/R² minima. Those windows are support checks, not proven
independent maneuvers. Random predictor handling assumes independent-error direction; correlated
errors, model/alignment bias and coverage remain unvalidated. Analyzer/fit now expose explicit
`forward_reference='matched'`, requiring research candidate and measured forward uncertainty.
Default legacy reference remains unchanged. The method/policy are in inference provenance;
the new module is source-hashed. Research CLI accepts `--forward-reference matched`.

No fresh flight, science fit, search, calibration or validation ran. Saved-data
`docs/airline-pilot-preparation-20261006/forward-uncertainty-review.json` reports sigma
0.010193 rad (0.58402°), gain 0.925229 and R² 0.897332, without rerunning the science fit.
Controlled SciPy-frame tests include continuous sub-degree bank corrections, body-yaw changes,
a larger transient, GPS/gyro noise and correlated gyro disturbance; covariance/gap/rotation/
negative controls and engine propagation are checked. A fixed eight-noise panel is software
verification, not coverage evidence. Focused integration: **102 passed in 4.73s**; subsequent
matched-method tests including body-yaw/transient stress: **11 passed in 0.37s**. No full suite.

Qualitative footage context: 135 mm lens, QHY585 mono camera, infrared recording through
right-side passenger window; frequent apparent motion below a degree, occasional larger view
changes. No footage ingested, calibrated aircraft attitude inferred or optical timing aligned.
Use this to motivate physical motion tests; do not call all short variations GPS noise or
equate image motion directly with course/bank without mount/timing/calibration.

New documented corpus `docs/matched-airline-pilot-20261006/`: README.md, plan.json and
preparation-review.json. Helper `analysis/tests/prepare_matched_pilot.py` freezes fresh seed
600901, the explicit C2 FRA–JNB route, three candidates using matched measured reference,
three truths × two composite wind/bias scenarios, 18 planned evaluations. Initial three are
proposed only, zero authorized, no run directory/worker. Original failed attempts stay spent.
New source: `82c882d2abf351cb0feb0e8efa237702d1deeccd475d682960419677bf479412`.
Plan: `e3064a50835a631d6968b11757d8451cff1e87c20e9ae74bf02580f2fa06bf78`.
One-thread environment unchanged: `20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`.
All older prospective plans remain historical/incompatible. Next is a separately authorized
three-attempt full-pipeline runtime/separation pilot, two single-thread workers maximum.
Then review failures/geometry/pair evidence before approving the remaining 15 or another plan.
No wall-time ceiling or successful-fit runtime estimate exists. All git operations still
need fresh consent. Documentation/readiness record this unrun proposal and provisional status.

**Latest saved-data diagnosis and smoother-route extension:** no new flight attempts, science
fits, search, calibration or validation were run. New helpers `analysis/tests/audit_roll_proxy.py`,
`forward_smoothing_diagnostic.py`, `prepare_smooth_route.py`; focused tests
`test_roll_proxy_audit.py`, `test_forward_smoothing_diagnostic.py`, `test_smooth_trajectory.py`.
The documented airline-pilot corpus additionally contains `roll-proxy-review.json`,
`matched-smoothing-review.json` (first diagnostic), `matched-smoothing-support-review.json`
(final gap-hardened result), `smooth-trajectory.json` and `smooth-route-review.json`.
Saved GPS/scalar-roll R² is 0.012284 versus 0.278223 with assumed noise-free GPS. PCHIP
position curves imply discontinuous bank: max 15.9084° at knots; 20 Hz scalar roll extrema
−162.189/+23.508°/s. This is an assumed interpolation artifact, not measured aircraft motion.
Research-only common 30s Hann filtering gives gain 0.925229, R² 0.897332 over 4,187 supported
windows. It has no angle uncertainty, science acceptance or empirical threshold. Default
forward estimation and eligibility are unchanged. GPS predictor error and correlated-filter
uncertainty must be addressed before integrating it into inference; do not inject known axes.

Explicit `trajectory.smooth_track_spec` returns version `observed-trajectory-replay-2` with
natural C2 cubic curves per existing support block. Version 1 stays PCHIP; no silent upgrade
or gap bridging. Observations/heights remain exact; endpoint curvature and possible overshoot
are declared assumptions. Prepared FRA–JNB alternative hash
`5e69715fb544fd45612318a48f15136f7df97354289ecfdbc939e7dc16229d83` has scalar roll extrema
−0.186935/+0.330154°/s at 20 Hz, but has not generated a flight or demonstrated model separation.
This changes current scientific source to
`3b42547d5a2ffa2a2ef5d975382b4b1b2b0a762fe831493d40cb1b7f469cb682`.
Old completed pilot keeps its d5d63a6 freeze and all original failures; prospective plans need
refreezing before execution. Focused verification: **51 passed in 2.39s** (new diagnostics/C2,
core pipeline, processing audit and original preparation). No full-suite rerun. All allowances
remain zero; no active worker. Next: uncertainty-aware matched reference with independent
GPS/gyro/gap controls, then a newly authorized, refrozen smoother-route full-pipeline pilot.
Docs/readiness updated; these additions remain uncommitted and git needs fresh consent.

**Subsequent airline-pilot preparation:** continuation reviews provisional wind/TAS and mount
assumptions without flight fits, SVDs or optimizer search. New preparation-only helper/checks:
`analysis/tests/prepare_airline_pilot.py`, `analysis/tests/test_airline_pilot_preparation.py`.
New documented corpus: `docs/airline-pilot-preparation-20261006/README.md`, `plan.json` and
`assumption-review.json`. Five prepared archived routes are reviewed using the assumed smooth
path only. Original public observation intervals, speed discrepancies, buffered turn checks,
65 frozen physical-envelope speed residuals and prescribed-wind latent TAS knot mismatch are
diagnostics, not measured receiver accuracy, science retention, reconstructed orientation or
grounds for pruning inconvenient states. Scientific algorithms/priors/constraints are unchanged.

The unrun sharded development plan proposes one fresh seed 600900, FRA–JNB simulated frequent
GPS, IMU turns 20/40/60 minutes, three truths, wind+mixed bias and wind+mixed bias+correlated+thermal,
and three fit candidates: wind/exclude, wind_tas/exclude, wind_tas/model_and_compare. Dynamic
bias, axis/segment weights, measured forward uncertainty, envelope and direct pair profiles;
bootstrap zero. There are 18 evaluations of six generating conditions with shared streams,
not 18 independent null draws. The initial proposed prefix is **3 evaluations** of the same
rotating-globe wind+mixed-bias condition under the three candidates, to measure new time/storage.
These are proposals only: no candidate/domain/threshold promotion and **zero authorized attempts**.
No runtime quote can use old 7–12-second measurements for the much larger envelope/dual-path
calculation. Preparation requires one numerical thread and freezes the current source/config/
policy/environment. Future execution needs a new explicit bounded budget. No git operation is
authorized by preparing this plan. Keep earlier wind/core proposals historical.

Preparation completed with six checks passing in 1.07s and no flight/SVD/search. Current science
hash remains `d5d63a6eec604ac2ba02cb39648767a914841f3c05bb8790eeb1ef442f95cb42`;
one-thread environment `20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`;
plan `74b7de930a28daeb5dc56884f1baefc990a32c1bcc68b285ea33ef6c4a75bfe7`.
Turns pass the assumed buffered mask for FRA–JNB and SEA–KEF, fail for the three supplied windows.
FRA–JNB prescribed-wind knot-interpolation mismatch is median 2.95, p95 11.41, max 20.68 m/s;
79.7% of sampled supported path points fall within 6 m/s. Other maxima are 23–49 m/s. These
include potentially excluded intervals and are not a fitted/optimal spline residual, measured
airspeed or proof of model failure. All 65 physical grid states fail the every-sample 6 m/s
diagnostic on each reviewed path; off-manifold combinations remain, no envelope pruning.
No strict wall-time limit exists in this proposal; implement one before claiming a time-capped
execution budget. The initial three-evaluation budget still awaits explicit authorization.

**Subsequent saved-processing audit (no additional flights or fits):** the user authorized
the proposed diagnostic work after publication of `314c1b7`. New tool/tests:
`analysis/tests/audit_processing.py`, `analysis/tests/test_processing_audit.py`.
New documented artifacts: `docs/protocol-development-20261006/processing-audit.json` and
`PROCESSING_REVIEW.md` in that directory. Eight focused checks passed in 0.23s.
Combined processing and prior geometry-audit verification: 17 checks passed in 0.26s;
reader links, Python syntax, current source hash and zero additional-attempt allowance verified.
The independent fixtures use SciPy rotations, known axes and small coordinated maneuvers,
not the flight synthesizer or nonlinear fitter. Basic frame reconstruction agrees to numerical
precision; clean turns recover orientation. An overlapping 3°/s aircraft yaw causes 14.85°
mount-mapping error without a gap warning; overlapping bank produces 7.46° error.
Nominal horizontal forward-axis errors in saved revised/original cases are 4.82–5.21° versus
under 0.2°, with revised reported sigma 1.47–1.51°. Nominal geometry is diagnostic, not exact
historical orientation truth; summaries omit raw gyro/bins/mount matrices needed to isolate cause.
All 72 have zero watchdog exclusions. Before/after science-cutoff all-contrast passes are
original/dynamic 18/18 -> 18/18, original/wind 14/18 -> 9/18, revised/dynamic 18/18 -> 0/18,
revised/wind 0/18 -> 0/18. Do not treat cutoff-only failures as absence of all projected
information, or relax cutoff/nuisance gates to manufacture success.
An unrun timing-only proposal uses 5/25/40/55/70/80 minute IMU turns on the same 90-minute
route, avoids known aircraft-turn overlap, and passes coarse known-axis tangents at all anchors
and both crab fits. Its worst retention is only 0.3274 versus 0.31225 cutoff. This is neither
an optimized protocol nor a simulator/real-IMU guarantee. Next define a turn-overlap/orientation
safeguard, then obtain a separate small campaign budget retaining raw sessions, bins and mount
matrices to isolate the mechanism. No scientific source, gates or thresholds were changed.
The user authorized committing the audit and follow-up documentation as one unit.
Pushing that commit or subsequent git operations requires separate explicit consent.

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

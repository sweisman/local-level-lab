# Recovery for the observed dispatch study

The sixteen-case ESA method study permits an unchanged-input technical
continuation only for tasks left unfinished by a worker or host interruption.
Every sealed numerical pass and failure remains final. An interruption never
resets charged calls or the original 30-hour wall allowance.

Before launch, qualify `lll.studies.task_resume` with its source-bound five
reboot and mutation checks. If a reboot occurs, use
`~/venv/bin/python analysis/status.py --study data/esa-observed-model-dispatch-globe-pairs --recovery`
to inspect saved results, leases and work charges. Verify that workers have
stopped through the study runner; a stale PID alone is insufficient.

Only after verified worker exit, close the original run terminally using the
qualified recovery request. Prepare a separate continuation with at most
**three starts per unfinished task**, **sixteen charged technical interruptions
in total**, **30 additional wall hours**, **four one-thread workers** and a
**5 GiB minimum free-space reserve**. The continuation must bind the unchanged
source, input and environment hashes and inherit the original per-task native
call and packet-visit limits. Its resume command is idempotent and must be
run through the four-thread compute guard. Use the `task_resume` CLI's
`close-original`, `prepare` and `resume` commands with the exact parent and
new continuation identity only after its evidence check passes.

This policy does not permit a new start for a completed numerical failure or
an increased scientific work allowance. Preserve journals and partial
artifacts until verified study closure and publication.

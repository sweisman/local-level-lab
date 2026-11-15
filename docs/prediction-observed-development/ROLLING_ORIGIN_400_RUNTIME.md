# Earlier-origin study execution

The [planned 400/120 cut](ROLLING_ORIGIN_400_PLAN.md) and its
[saved-input preflight](ROLLING_ORIGIN_400_PREFLIGHT.md) are prepared as a
two-task, source-bound study. The fitting worker receives the first 400
receiver positions, the IMU packets through report 519 and forecast times;
it receives no future receiver positions. The two declared error laws each
get one start and the original 200-evaluation rule. The original study allows
two one-thread workers for four hours. A separate frozen policy permits
recovery of unfinished tasks within two technical interruptions while
preserving completed outcomes and work charges.

The canonical status command is:

`~/venv/bin/python analysis/status.py --study data/esa-rolling-origin-400-development-v1-20261115`

After a reboot, the idempotent recovery entry is:

`~/venv/bin/python analysis/tests/run_numerical.py --workers 2 --threads 1 -- ~/venv/bin/python -m lll.esa_rolling_origin_400_recovery resume`

The original fit phase is complete: both tasks passed numerical checks with
eight evaluations each, no active bounds and no worker errors. That is a
fit result, not a withheld prediction score. The separate
[conditioning plan](ROLLING_ORIGIN_400_CONDITIONING_PLAN.md) passed eight
focused tests and five recovery tests. Its prepared manifest contains only
the first 400 receiver reports, the saved fits and forecast times. Its own
recovery policy is frozen. Both tasks sealed and their saved training costs
and covariance normalizations replayed exactly. The separate
[withheld score](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md) gives 0.56 m
horizontal and 0.17 m height RMS after conditioning, compared with 5.38 m
raw horizontal RMS. The result is one exploratory development window;
coverage and physical adequacy remain unqualified and no Earth-model
decision follows. Seven reserved ESA flight groups remain closed.
The [fit evidence](rolling-origin-400-fit-evidence/README.md) and
[conditioning evidence](rolling-origin-400-conditioning-evidence/README.md)
are packed in the verified archive. Recomputing the score from those archived
studies produces the same SHA-256 result:
`31ecc2f2ea657aa2be2b63f83656e5fda35decfcd17247145766771dea5294e6`.
Portable copies contain their source snapshots, inputs, task journals and
completion receipts without depending on the shared archive catalog:
[fit bundle](rolling-origin-400-fit-evidence/bundle.zip) (SHA-256
`1a2e5e8c4b98b8cac4ce5d01cf85aa48178a8c4f7bcc5f546fa54074ab26a851`)
and [conditioning bundle](rolling-origin-400-conditioning-evidence/bundle.zip)
(SHA-256
`54733f07807e49931bab73cc79f6c2a70be6c621e88d1fd4edeb6a373ba17df6`).
Verify either with
`~/venv/bin/python -m lll.studies.portable verify <downloaded-bundle.zip>`
after installing the analysis package.

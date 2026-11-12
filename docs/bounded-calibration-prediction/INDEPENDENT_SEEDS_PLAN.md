# Independent-seed method check

Question: does the existing bound-aware two-minute aircraft procedure retain
numerical completion, withheld-position accuracy and manageable interval
widths when its noise realization changes? The 24-case development release
used one shared seed. Its 2,880 coordinates are not independent trials.

Use the same three physical models, both processing cases, both declared IMU
error-input laws and interior/Z-gyro-boundary calibration cases. Run the full
24-condition matrix for each of two **new** independent generator seeds,
`314159` and `161803`: 48 separately identified tasks. Do not adapt seeds,
models, bounds, receiver policy, height profile, timing convention or the
200-evaluation ceiling after inspecting results. Preserve the original
development release and its one failed stopping outcome.

Reuse `lll.bounded_nonlinear_study.run_case` and shared generators; add only a
small adapter that binds each task to its own seed. Require separate IMU and
receiver random streams as in the existing generator. Keep later truth and
receiver reports withheld until the forecast and both uncertainty targets are
sealed. Save all failed tasks. Use four workers with one numerical thread each,
and a finite five-hour study wall limit. Each task has the original per-case
maximum of 200 fit evaluations, 239,816 low-level native calls and
1,506,051,012 packet visits. Actual work is charged before execution. Qualify
task-level interruption recovery before launch; never rerun a sealed failure.
If the notebook reboots, first verify the original manifest, journals and
sealed results. The generic `lll.studies.task_resume` recovery is already
qualified on source-bound interruption controls. A separate continuation may
then be frozen for only unfinished identities, with at most **three charged
technical attempts per identity**, **24 total technical interruptions**, a
new finite **five-hour wall limit** and a **5 GiB free-space reserve**. Its
`resume` command is idempotent: it verifies existing stages and never
re-executes a sealed result. A scientific failure remains sealed and is not
retried. The continuation has its own charges; it never borrows unused work
from the original allowance.

Report, by seed and condition, technical completion, numerical stopping,
withheld-position accuracy, bound activity, coverage of physical position and
future receiver reports, and interval width. A failed numerical or accuracy
screen remains a failed method check even if its interval contains the later
truth. **48/48 combined passes** are required before planning a larger
coverage campaign. Even 48/48 cannot establish nominal 95% coverage: there
are only two independent noise draws per condition and many correlated epochs
within each draw. All scientific decisions abstain.

This study is generated-data software qualification only. It does not inspect
an observed or protected flight, estimate actual device limits, select an
Earth model or authorize a receiver threshold. Any later statistically sized
coverage campaign needs its own frozen acceptance, width and sample-size rule.

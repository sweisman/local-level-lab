# Native packet-boundary adapter comparison

Use the first 16 packets from the same six qualified generated histories.
Preserve original configurations and calibration scales. At zero normalized
parameter value, query the represented endpoint of packet 6 and its immediate
binary64 predecessor and successor. The native ≤ rule assigns the first two
queries to packet 6 and the successor to packet 7. Preserve all three queries.

Each case makes one native batch with three outputs and their 27-column
Jacobians. For each query, calculate all 27 unit parameter directions with the
successor interval adapter and its declared packet owner. Compare native values
and branch first derivatives with the intervals, using the same fixed local
scales and one-micrometre software tolerance as the earlier adapter studies.

The successor preserves the native upper fraction guard instead of clipping a
fraction slightly above one. It rejects wrong packet ownership and supports an
explicit one-sided request separately. Known-answer tests cover the one-sided
formula; this native comparison checks the branch chosen by the native code.
At a switch these are branch derivatives, not a claim of global smoothness.

| Resource | Per case | Total maximum |
|---|---:|---:|
| Fixed started identities | 1 | 6 |
| Native batches / queried epochs | 1 / 3 | 6 / 18 |
| Conservative native packet visits | 48 | 288 |
| Interval calls / packet steps | 81 / 513 | 486 / 3,078 |
| Value / branch-derivative comparisons | 243 / 243 | 1,458 / 1,458 |

Use one numerical thread, reserving two for the existing long-record study.
The cooperative ceiling is 30 seconds per bound and 600 seconds overall.
Freeze full source/input/environment/compiler closure, charge before execution,
retain failures and permit no retries, signals or budget changes.

Passing qualifies these short boundary cases only. Full clock support,
incoming trajectory and rotation jumps, useful whole-history ranges, native
execution-error bounds and an aircraft error law remain separate requirements.
There are no aircraft-original reads or optimizer starts. Publication performs
no new evaluations.

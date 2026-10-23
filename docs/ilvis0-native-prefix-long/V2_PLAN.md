# Corrected long-record comparison

The question and acceptance rules are unchanged: on all six fixed generated
histories, does the reused calculation reproduce the complete original bounds
at 290 and 438 seconds, including all 51 calibration/source columns?

The first freeze has an artifact-writing incompatibility. Its started original
reference calculations finish without interruption; its sources, outcomes and
charges remain preserved. This corrected freeze repairs phase-record names and
tests them with the framework's real immutable writer.

## Reuse complete answers; preserve failures

The saved 438-second references retain their original input, proof, source,
compiler and environment checks. A completed 290-second original answer from
the first attempt may also be reused after checking its closed completion,
sealed artifact, known adapter fingerprint, original-code hash, input/proof
bindings, elapsed time and peak memory. A charged call or partial file alone
does not qualify. The failed study does not acquire a successful label.

An identity not previously charged for an original calculation has one fresh
290-second call. If an early answer is reused, the new identity has **zero**
such calls. A previously charged but incomplete original call blocks this
bookkeeping-only repair; it cannot silently be retried. Freeze each case's choice
before execution. Do not recalculate a reused answer or transfer unused allowance.

## Fixed limits

| Resource | Limit |
|---|---:|
| Cases | Six: three candidates × two processing treatments |
| Packets per case | 96,000 |
| Independent point/Jacobian checks | Two per case; twelve total |
| New batched calculations | One per case; six total |
| New original-cold calculations | One only for each case lacking a verified early reference |
| New diagnostic calls per case | One if both originals are reused; otherwise two |
| Conservative bound steps per case | 1,728,000 if both originals are reused; otherwise 2,592,000 |
| Actual batched packet advances | At most 192,000 per case |
| Fresh original-cold call | At most 7,200 seconds |
| Batched call | At most 14,400 seconds |
| Peak resident memory | At most 1,536 MiB per worker |
| Allocation | Four workers × one numerical thread; four total |
| Whole-study wall ceiling | 86,400 seconds |

The executable manifest records the exact totals after reference verification.
With four reusable early answers, this is eight new diagnostic calls and
12,096,000 reserved bound steps. Prior charges are reported separately.

Resource checks remain cooperative; processes are never signalled or killed.
Prepay batch work, check limits before each step, and retain the complete
reservation after interruption. Phase records have distinct immutable names.
Only scheduling may change to balance the known fresh-reference workload.
There are no retries or later increases to this allowance.

## Success and remaining work

All six cases must match both complete original reports and all 51 coefficient
columns. Independent center checks retain the 10-micrometre software allowance.
Save actual time, memory, packet work and every failure. Historical reference
times are not a controlled speed benchmark; reused work is never reported as
zero-cost original computation.

Passing qualifies reuse on these controls. It does not establish useful full
prediction ranges, actual measurement noise or calibrated observational coverage.
The 53-stretch findings and protected confirmation flights remain unchanged.

[Original scope](../ilvis0-native-prefix-long/PLAN.md) ·
[Repair rationale](../ilvis0-native-prefix-long/RECOVERY_PLAN.md) ·
[Short controls](../ilvis0-native-prefix-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

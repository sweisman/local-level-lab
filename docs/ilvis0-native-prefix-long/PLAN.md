# Long-record reuse: frozen comparison scope

This software study checks whether the faster calculation preserves the original
answer over long histories. It performs no aircraft fits and changes no scientific
assumptions or selected flight intervals.

## Fixed comparison

- Six existing generated histories: three candidate models under both processing
  treatments, each with 96,000 packets and the same final training-conditioned proof.
- Two queries, at 290 and 438 seconds. Preserve the complete reports and all
  51 coefficient columns, including all 27 physical calibration parameters.
- Reuse the saved original 438-second answer only after verifying its source,
  inputs, calibration region, proof, compiler and numerical environment. Storage
  and test changes are recorded separately; original numerical helpers must agree.
- Calculate one fresh original answer at 290 seconds using the final proof.
  Compare both answers with the new batched calculation. Two independent native
  point/Jacobian calls check the centers with the existing 10-micrometre software
  allowance. This allowance is not aircraft measurement precision.

## Finite execution limits

| Resource | Per case | Whole study |
|---|---:|---:|
| Identities | 1 | 6 |
| Independent point/Jacobian calls | 2 | 12 |
| New diagnostic calls | 2 | 12 |
| Conservatively reserved bound steps | 2,592,000 | 15,552,000 |
| Actual batched packet advances | At most 192,000 | At most 1,152,000 |
| Reused original answers | 1 | 6 |
| Original cold calculation | At most 7,200 seconds | Six separate calls |
| Batched calculation | At most 14,400 seconds | Six separate calls |
| Peak resident memory | At most 1,536 MiB per worker | Four workers at most |
| Wall allowance | — | 86,400 seconds |

Run four workers with one numerical thread each: four total. Each identity is
charged before execution; no retries or allowance expansion. Batch work is
reserved in advance, then checked locally before every step, avoiding a disk
transaction for every packet. Interrupted work retains its complete reservation.

Deadlines and memory checks are cooperative. The original cold routine checks its
own time allowance; peak memory is checked at phase boundaries. Batched work also
checks memory and the study deadline at least every 256 packet advances. Processes
are never signalled or killed to enforce an allowance. A returned over-budget
calculation is a failure, not permission to enlarge the budget.

## Cost and interpretation

Saved 438-second calculations took about 110 minutes each. The new cold plus
batched work is estimated at roughly three hours per case, about six hours in two
waves, with substantial runtime uncertainty. Historical times are not a controlled
same-run speed comparison. Save actual elapsed time, peak memory and packet-work
counts whether the comparison passes or fails.

Success requires equality and bounded resources for all six cases. It qualifies
this reuse method on the fixed controls, not a useful whole-record prediction
range, actual sensor noise, independent statistical confidence or a new aircraft
finding. The 53-stretch results and reserved ESA confirmation data are unchanged.

[Long comparison design](../ilvis0-native-prefix-controls/LONG_PLAN.md) ·
[Short comparison](../ilvis0-native-prefix-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

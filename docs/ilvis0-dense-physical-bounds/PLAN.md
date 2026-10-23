# Full-cadence prediction: training bounds

This stage calculates a conservative prediction envelope at every earlier
measurement time. It uses six generated eight-minute IMU histories: all three
physical candidates, each under both processing assumptions. No aircraft
originals or protected ESA confirmation data enter this software study.

The complete experiment keeps 289 earlier epochs, from 2 through 290 seconds,
and 147 withheld later epochs, from 292 through 438 seconds. Its four declared
noise laws and original 20/20/50-metre prediction-width targets remain unchanged.

## What this stage does

Keep all 27 physical calibration parameters over their original normalized range
of −1 to +1. Construct the reference at the fixed zero vector. Use only the
independent physical-domain acceleration proof; no old one-metre training
constraints, generated truth or later observations may tighten these bounds.

Compute all 289 training envelopes per case using the qualified prefix-reuse
algorithm. Preserve each raw report immediately in one append-only, hash-chained
file per case. A completed prefix survives later failure but does not establish
study completion. Reject corruption or a truncated report rather than repairing it.

Reuse the sealed dense native predictions and Jacobians only after checking the
input hash, fixed point, exact times, compiler, source and numerical environment.
The original batch counter remains attached to its full batch; selecting earlier
epochs must not turn it into a newly interpreted subset counter. No new native
point integration is needed. Each envelope retains all 51 expression columns.

The reporting callback is isolated by copying its report. Removing its two
reporting-only statements and optional argument must reproduce the qualified
numerical source's syntax tree exactly. Small real integrations check all six
candidate/processing combinations, artifact writing and accounting before launch.

## Finite allowance

| Resource | Maximum |
|---|---:|
| Charged case identities / retries | 6 / 0 |
| Cached bound batches | 6 |
| Training reports | 1,734 |
| Native calls / optimizer starts / original aircraft reads | 0 |
| Packet advances per batch | 243,968 |
| Conservatively charged bound steps, all batches | 13,174,272 |
| Force-profile packet visits, all batches | 166,464,000 |
| Workers × numerical threads | 4 × 1 |
| Cooperative limit per case | 12 hours |
| Cooperative whole-study limit | 26 hours |
| Peak memory per worker | 1,536 MiB |
| Maximum report size | 1 MiB |

Per batch reserve 96,000 preparation packets, 27,744,000 force-profile visits,
96,000 prefix advances and 147,968 tail advances. Reserve 289 cursor copies,
867 source copies, 867 source-query checks and 289 reports. One bound step is
charged at nine times the advance allowance, preserving the existing accounting
convention. All reservations precede their associated work.

The prior two-query batches took about 95–99 minutes per case under a different,
data-conditioned proof. Here, advancing the heavy trajectory can be reused, but
each extra query still scans the complete force history. Expect several hours;
the limits allow two waves of work without relying on a precise extrapolation.
The limits are fixed before launch and cannot be expanded after an outcome.
Deadlines are cooperative; no process is killed.

## Acceptance and continuation

All six cases must finish all 289 epochs. Check source, frame, clock, reference,
full domain and data-independent proof at every epoch. Compare each center with
the sealed independent native calculation within the unchanged 0.00001-metre
software allowance. Preserve the raw center difference for later uncertainty
accounting; this tolerance does not prove a whole-program floating-point bound.
Retain every expression column and verify all resource counts.

Failures remain software limitations, not model rejections. Do not retry a
charged case, narrow the calibration domain or borrow an old training proof.

## Remaining stages of the complete experiment

1. Bind earlier observations under each of the four predeclared error laws,
   using separately frozen RNG streams and the predeclared nonzero generated
   truth. Keep later observations outside conditioning. Retain the single
   453-row error budget and all inherited typed constraints.
2. Freeze the next finite allowance before calculating conditioned envelopes
   across all 147 later epochs. Keep all candidate/processing cases and all four
   laws; an unsupported case cannot silently disappear from the comparison.
3. Seal forecasts before opening the later truth or observations. Check truth
   retention, prediction width, clock and native approximation allowances, and
   whole-period coverage. Preserve failed or overly wide results.

Passing this training-bound stage alone does not qualify withheld prediction,
actual instrument error laws, scientific significance or a new observed-data run.
The separate observational adequacy gate remains open even if the generated
complete-cadence controls pass.

[Acceptance requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Error-family and lineage requirements](../ilvis0-joint-projection-controls/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md)

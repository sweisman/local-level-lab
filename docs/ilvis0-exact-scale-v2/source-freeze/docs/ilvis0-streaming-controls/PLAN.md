# Streaming integration qualification

The long-recording infrastructure must reproduce the existing packet-by-packet
calculation without keeping a whole recording or its Jacobian in memory. This
is software qualification using generated measurements, not another archive fit.

## Implementation

1. Add separate C and C++ streaming wrappers around the unchanged native value
   and 27-column tangent kernels. A shared wrapper preserves calibration,
   geographic state, attitude, velocity and the exact per-packet elapsed clock.
2. Add `analysis/lll/ilvis0_streaming.py`: bounded-block inputs, strict ordering,
   finite-domain checks and hashed checkpoints tied to sources, environment,
   parameters, seed and caller-declared input identity. A rejected block cannot
   advance the state. No receiver positions or fused navigation enter this API.
3. Test values and every derivative against the existing whole-array kernels,
   including variable periods, chunk layouts, restarts, nonzero calibration,
   lever arms, all three models and both processing cases. At a block boundary,
   preserve the preceding packet and its start state: the original time-offset
   derivative uses the left interval. Averaging block periods is forbidden.
4. Freeze a generated-only finite comparison and scaling study after local
   tests pass. Publish verified results, limits and the remaining prediction
   gate. Do not run observed fits or inspect protected ESA results.

## Acceptance and limits

Exact same-library restart and chunk-layout outputs must match bit for bit.
Streaming results must match the unchanged whole-array value/tangent references
within 1 micrometre in local coordinate differences and 1e-7 metres per normalized
parameter in derivatives. Independent constant-pose controls must remain within
1 micrometre. Boundary counts and all 27 columns must be preserved.

The freeze has 48 generated identities: 24 matched value/tangent comparisons,
18 independent constant-pose controls and six scaling cases (30,000, 120,000 and
480,000 packets in each mode). Limits are 2,500 native calls, 3,000,000 packet
visits, 1,024 packets per scaling block, four total numerical threads and 600
cooperative wall seconds, with no retries. Calls and packet visits are charged
before evaluation. A failed control blocks remaining identities. It must
demonstrate bounded working memory and report measured runtime;
it does not establish feasible optimization of a complete eight-hour recording.

Streaming equivalence does not fix the overly wide recording-scale uncertainty
bounds, qualify actual covariance assumptions, establish withheld predictive
adequacy or authorize ESA confirmation. Those remain separate roadmap gates.

The generated scaling control accepts at most 8 MiB of traced working allocation
and a constant native state size. Reference comparisons and compilation are
outside that memory measurement. Native integration is serial; the thread
allocation is a ceiling. No parallel speedup or whole-record fit time is assumed.

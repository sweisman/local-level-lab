# Repeated-history and packet-boundary qualification

Use generated increments only. This study checks composition of the qualified
geographic bounds through complete short histories, including receiver timing
whose uncertainty crosses packet boundaries. It does not qualify aircraft
uncertainty or a whole-record floating-point enclosure.

For each packet, the exact fraction is `clip((t-start)/duration,0,1)`.
Its global affine remainder is the maximum at the time-interval endpoints and
packet breakpoints, plus the propagated time-input remainder. At an internal
boundary, match the native tangent's preceding-packet convention. At time zero,
use its first-packet forward convention. Propagate every potentially contributing
packet with its same common time variable and shared calibration. Reject gaps,
unsupported time intervals and geographic-domain crossings without repair.

## Frozen matrix and comparisons

54 identities: three physical candidates, histories of 3/9/33 packets, fixed-zero
or profiled removal centered at one, and interior/boundary/multiple-boundary time
intervals. All 27 normalized parameter columns remain present. Broad calibration
limits match the geographic controls; different packet lengths and generated
increments exercise nonuniform sampling. Both hemispheres are represented.

Each identity has sixteen probes: all lower bounds, all upper bounds, the center,
an opposite timing endpoint with other parameters fixed, and twelve fixed-seed
points. Compare against the unchanged C full-history prediction and C++ tangent.
An independent reference uses matrix exponentials, linear solves and its own
trajectory formulas; it never calls the bound calculation. Its complex-step
derivatives keep the selected packet fixed at exact boundaries, checking the
native one-sided convention rather than claiming differentiability there.

Native/reference position tolerance is 1e-6 m, in a fixed metric at the initial
location. Velocity tolerance is 2e-8 m/s, rotation tolerance 2e-10, and Jacobian
tolerance 2e-5 m per normalized parameter. Remainder checks add those arithmetic
tolerances and `2e-12*norm(linear_term)`. Record roundoff-limited checks separately.
Report the full-box change and remainder in metres, including conservative
growth; successful containment does not imply useful aircraft precision.

## Finite allowance

54 identities, 864 probes, 918 C full-history calls, 54 C++ tangent calls and
2,376 independent reference calls. One worker, four numerical threads, 300
cooperative seconds, no process signals. Reserve complete per-identity calls
before execution; interrupted charges are not refunded. No original reads,
archival native sweeps, optimizer starts, retries or protected outcomes.

Freeze source, compiler binaries/flags, generated-case identities and numerical
environment before launch. Preserve all failures and verify published hashes.
Long-record arithmetic, usefulness at recording scale and shared observational
error assessment remain requirements before another observed prediction trial.

[Geographic controls](../ilvis0-geographic-step-bounds/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

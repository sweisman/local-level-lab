# Planned finite starting-bound check

This is a software preflight for the complete-cadence prediction experiment.
It reads generated IMU histories, not retained aircraft originals or protected
ESA confirmation observations.

Use all six unchanged 96,000-packet cases from the earlier generated-history
study: three physical candidates and two processing assumptions. Preserve their
configuration, increments and timestamps. Select no case from its fit outcome.

Construct a new reference at the fixed zero normalized parameter vector over
the original full normalized physical range, −1 to +1 on all 27 parameters.
Keep each configuration's original physical scale factors. Use the independent
physical-domain acceleration proof, with no training inequalities, old one-metre
certificate, later receiver observations or known-truth constraint.

At the first declared training epoch, two seconds, save the independent native
point/Jacobian and the ordinary cold bound. The bound must not use that point
check as an input. Record all failures and charges.

| Limit | Maximum |
|---|---:|
| Generated histories / charged identities | 6 |
| New native point calls | 6 |
| Conservatively charged native packet visits | 576,000 |
| Cold-bound calls | 6 |
| Conservatively charged bound steps | 5,184,000 |
| Workers × numerical threads | 4 × 1 |
| Per-bound cooperative time limit | 600 seconds |
| Whole-study cooperative limit | 3,600 seconds |
| Peak memory per worker | 1,536 MiB |
| Original aircraft reads / optimizer starts | 0 |
| Retries / expansion | 0 |

The bound-step reservation is nine times the complete 96,000-packet input per
call, even though the query uses only its initial portion. Prepare and verify a
separate source/input/environment freeze before launch. Check the actual frozen
adapter under the worker's module-loader name before any worker starts.

Acceptance requires a physical-domain proof with no training-data premise,
unchanged full calibration ranges and center, the correct source/time/frame,
all 51 coefficient columns including all 27 physical parameters, and agreement
with the independent native point within the unchanged 0.00001-metre software
arithmetic allowance. Time and memory must remain within the frozen limits.
An unsupported source or failed check is a software limitation, not rejection
of an Earth candidate.

All six cases must pass this preflight. Passing only establishes that the
independent starting calculation is supported. It does not qualify the later
289 training queries, 147 forecast epochs, complete prediction uncertainty,
actual noise assumptions or the observational two-stage decision procedure.

If a starting proof is unsupported, investigate it in a separately identified
version. Do not import an old data-conditioned proof, narrow calibration ranges,
change the numerical allowance or relabel a failed case to obtain a pass.

The complete experiment still needs its own costed freeze, matched declared
error families, fresh conditioning from the actual training rows and full-period
prediction checks. No additional allowance follows from unused preflight limits.

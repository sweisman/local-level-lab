# Complete optimizer qualification after feasible linear initialization

The linear correction passes the independent convex controls and the matched
four saved matrices. The next gate tests the complete fitting and verification
procedure, rather than its linear component alone.

Use the shared analytical control families: 36 fits across nine known-answer
objectives and four prescribed starts, plus eight direct accept/reject probes.
Retain nonoptimal starts, rank deficiency, active bounds, timing corners and
physical-change checks. Reference minima are specified independently of the
fitter. This is a fresh execution with the revised source, not a restart of the
earlier local-anchor qualification.

Freeze 44 identities, one numerical thread, a 600-second cooperative ceiling,
at most 7,488 analytical evaluations and 22,500 bounded linear operations. The
shared per-case allowances and charges remain in force. No native integrator
calls, generated IMU histories, original observations or protected data.

Require every known-answer fit and direct probe to behave correctly, and all
nine start groups to agree under the existing objective and position limits.
Record failed and unexecuted cases without retries. Source-bound software checks
and an environment freeze precede execution. Independently audit, publish and
compact the result using the existing common worker and reporter.

A successful analytical outcome permits preparation of a separate finite
native trial. It does not reopen calibration or establish statistical coverage.

[Linear correction](timing-linear-anchor-check/INTERPRETATION.md) ·
[Current roadmap](ANALYSIS_ROADMAP.md).

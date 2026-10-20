# Chunking preserves the existing integration

**All six separate controls pass.** The longest reference comparison contains
480,000 packets: 26.7 minutes at nominal 300 Hz. Both streamed value calculations
and all 27 derivative columns match the unchanged whole-array kernels exactly
at every tested query, including a mid-record serialized restart.

The earlier 400-second exact-pose discrepancy is present identically in the
original kernel: **3.48 micrometres** in both calculations. At 1,600 seconds,
both show **0.223 millimetre**. Chunking adds no observed discrepancy. The
separate exactly representable stationary controls remain exactly at their
target through 480,000 packets in both modes. No kernel or tolerance changed.

The first study's failed absolute-pose criterion remains failed. The present
result qualifies streaming equivalence on these generated cases, not an
absolute floating-point enclosure or a universal whole-record accuracy claim.

Traced streaming working allocation stays below **0.7 MiB**. Native state is
560 bytes for values and 14,168 bytes for the 27-column tangent. The streamed
480,000-packet comparisons take 8.7 seconds for values and 23.6 seconds for
derivatives on this machine. Reference storage, compiler and shared-library
storage are outside the traced working measurement. These are serial passes,
not measured eight-hour fit times or four-thread speedups.

Together with the structured-covariance prerequisite, this closes L01's current
software-equivalence task. Actual rate sampling, continuity and error assumptions
still need qualification before long ESA model fits. The overly wide nonlinear
prediction bounds and absolute withheld adequacy remain separate scientific
gates. No archival result or production decision changed.

[Measured results](README.md) · [Frozen scope](PLAN.md) ·
[Preserved earlier failure](../ilvis0-streaming-controls/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

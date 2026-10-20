# Correct completed checks, but the implementation is too slow

Twenty of the 24 controls pass. The four broad globe cases reach the unchanged
per-bound time limit, so the complete candidate does not qualify. All six
derivative controls, all six packet-boundary controls, all six stationary-motion
controls and both broad flat-disc controls pass.

The implementation carries separate coordinate bounds through velocity and
position calculation while keeping the existing global norm bounds. It retains
the original model equations, centers, training-conditioning path and all
physical/shared columns. Local training-region tests also pass. This is useful
implementation progress, but it is not a qualified replacement for the complete
prediction method.

A single, shortened generated-data performance probe identifies repeated exact
rational construction and repeated validation of already immutable arrays as
major costs. It used 32 packets and a fixed clock for profiling only; it is not
a retry of a failed study identity or a scientific acceptance test.

The next candidate will reuse immutable validated views and cache repeated
exact norm calculations. The rational arithmetic and its resulting bounds must
remain unchanged. Independent tests compare all returned bounds bit for bit
with this reference. Qualification requires a new freeze under the same limits;
the completed study and its four failures are preserved.

[Results](README.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

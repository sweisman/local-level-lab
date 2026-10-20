# Qualify every source prefix without a recording-size derivative tensor

Use the same six generated sources and sector-4 reference points as the
completed source-reference comparison. Stream the body rotation and all 27
physical reference columns through every packet. Return `A=R f` and
`B=R(P−I)f` at that packet's actual midpoint and endpoint.

The compiled source uses the unchanged native Dual, calibration and exponential
primitives. Its state is bounded below 16 KB regardless of recording length;
do not retain a tensor of all recording derivatives. Retain immutable copies of
the packet inputs used by the stream, and enforce its finite packet allowance.
Preserve the native clipped clock branches, including the preceding packet's
slope at an exact endpoint and the first packet's forward slope at time zero.

Independently stream quaternion rotations and analytic rotation Jacobians.
Check every source value and all 27 coefficient columns at both phases of every
packet. Value tolerance remains 1e-10 m/s²; coefficient agreement remains
absolute 2e-10 plus relative 2e-8. Unused columns must remain zero. Local tests
also compare both implementations with complex-step matrix exponentials,
nonuniform periods, exact clock boundaries and caller-mutation controls.

Finite allowance: six identities, six setups, 9,600 native source steps,
9,600 independent steps and 3,225,600 scalar comparisons. Each identity has
exactly 1,600 packets and is charged its steps before execution. Four workers
use one numerical thread each, with a cooperative overall limit of 180 seconds.
No retries, extensions, full native trajectory calls, propagation bounds,
optimizer starts, original aircraft reads or protected ESA data.

Preserve hashes of all streamed value/coefficient arrays plus selected first,
last and active-clock prefixes. Compiler, sources, inputs, environment and
allowances are frozen before execution. Prefix comparisons qualify only this
reference component, not whole-program floating-point enclosure or observation
coverage. Connecting the tighter source interval and qualifying the complete
native prediction method remain separate tasks.

[Source reference](../ilvis0-source-reference/README.md) ·
[Qualified transport](../ilvis0-cached-transport-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

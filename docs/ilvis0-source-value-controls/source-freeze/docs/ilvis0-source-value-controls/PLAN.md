# Physical source intervals at every packet prefix

The compiled transport and six-source runtime screen are complete. The new
physical-source stream adds explicit calibration, rotation-center and matrix
arithmetic allowances. Local checks include point domains, all 27 parameter
directions, clock crossings, both packet phases and a nonexact mount matrix.

This qualification reuses the same six generated 1,600-packet sources, original
reference points and saved physical parameter bounds. It constructs physical
intervals for `A = R f` and `B = R(P − I)f` at every midpoint and endpoint.
It checks that the unchanged compiled source references lie inside the actual
reported allowances, with no extra comparison margin. It also checks the
norm-identity closure, including the literal installation matrix's metric defect.

This is a physical value calculation. It does not yet transfer the training
acceleration constraints, qualify reference-row/Taylor-error conversion, install
the body adapter or recompute complete position ranges. Those remain gates.
The existing trained-adapter point failures remain preserved.

## Finite allowance

- Six identities, six setups and no retries.
- Six complete source-value bounds; 19,200 midpoint/end bound steps.
- 9,600 compiled source-reference steps, 115,200 scalar comparisons and
  19,200 norm closures, reserved before execution.
- Four workers, one numerical thread each; four total threads.
- 120 seconds per identity, checked cooperatively, and 600 seconds overall.
- Zero full native trajectory evaluations, LP proposals, optimizer starts,
  aircraft-original reads or protected ESA data.

Freeze sources, generated inputs, compiler and numerical environment. Record
every reservation and failure. Compile numerical primitives from the frozen
source directory. Keep interval/reference stream hashes and selected prefixes;
do not store a recording-size derivative tensor. Every identity must complete
and pass before the physical-source component is qualified.

[Source rounding work](../ilvis0-body-interval/ROUNDING_PLAN.md) ·
[Completed runtime screen](../ilvis0-compiled-range-preflight/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

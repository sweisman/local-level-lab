# Source derivative component qualification

The completed long-history screen removes the time-limit failures but still
overstates horizontal error allowances. This separate component bounds source
derivatives on the physical calibration domain, so a mean-value calculation
can retain their linear information.

It uses interval automatic differentiation with all 27 physical columns, exact
literal inputs and outward binary64 arithmetic. Rotations use a finite series
with an explicit value and derivative tail. No accuracy bound for library sine
or cosine is assumed. The working state is fixed-size. Both midpoint and end
sources are retained. A clipped clock fraction includes both one-sided slopes
when the domain crosses a packet boundary.

Check five rotation vectors against independent exact-rational value and
derivative references, including zero, mixed axes and eight radians. Check a
13-packet zero-motion source, a four-packet nonzero source against rational
rotation predictions, a two-packet clock-boundary case, an independent cubic
mean-value example with displaced supplied center/rows, and invalid inputs.
Keep domain rejection, immutable storage and the finite packet allowance.

## Separate finite allowance

- Ten fixed known-answer identities; no retries.
- At most 26 charged compiled/component bounds and 85 logical bound steps.
- At most five source initializations, charged even on expected failure.
- Reserve 41 rational rotation/derivative references before their controls.
- Four single-thread workers; 120 seconds overall, checked cooperatively.
- No complete trajectory evaluations, optimizer starts, LP calculations,
  observed aircraft inputs or protected ESA data.

Freeze the tests, implementation, compiler, Python/test-package versions and
control catalog before launch. All identities and planned charges must pass.
These controls qualify the mathematical component on known answers. They do
not install a training constraint, establish useful complete prediction widths
or qualify native/observed propagation. Source/domain binding, training
intersection and full native qualification remain separate gates.

[Derivative-bound rationale](../ilvis0-batched-range-preflight/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

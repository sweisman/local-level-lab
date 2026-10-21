# Check the source value and derivative at the reference point

The tighter prediction method needs a certified link between its mathematical
reference and the numerical values used by the integrator. First check the
point-value and derivative component against a separate rational calculation.

Seven controls cover nonzero calibration, both packet phases, all 27 parameter
columns, noncommuting rotations, a nonorthogonal fixed mounting matrix, the
clock origin and packet boundaries, input ownership and invalid inputs.
Rotation references use a separate exact-rational series and chain rule.
At a clock knot the candidate must contain both one-sided derivatives,
including the preserved native preceding-packet convention.

## Separate finite allowance

- Seven identities; 20 point-source append calls and 20 packet steps.
- Six valid initializations, 115 rational reference calls, seven input rejections.
  Reference calls count derivative helpers and their nested value helpers separately.
- One worker and one numerical thread; 120 seconds, checked cooperatively.
- Code, tests, compiler, catalog and numerical environment frozen before launch.
- No retries, aircraft reads, trajectory evaluations, fits, LP proposals,
  protected ESA data, process signals or allowance expansion.

Require all controls and reservations to pass. Keep earlier source kernels and
studies unchanged. Passing qualifies the sampled component paths, not the
complete source-remainder bridge, native integration, useful prediction widths
or statistical confidence.

[Direct remainder construction](../ilvis0-eastward-growth/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

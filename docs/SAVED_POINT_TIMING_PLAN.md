# Next comparison: test the mechanisms at the saved points

**Active implementation plan.** The [small controls](timing-precision-controls/INTERPRETATION.md) identify two
mechanisms. The next bounded question is whether they account for the derivative
discrepancies in the four exposed development examples. This plan does not
authorize a fresh calibration campaign or change a failed fit into a pass.

## First qualify the alternatives

Use separate diagnostic adapters; leave the original wider kernel unchanged.

1. At an exact packet end, evaluate the timing slope approached from the
   feasible side of the time-offset bound. Preserve the original branch as the
   reference. Do not claim a single smooth derivative where two slopes differ.
2. Accumulate longitude relative to its initial value, restoring the coordinate
   origin for reported positions. The equations do not use absolute longitude
   to determine motion. Check residual subtraction, wrapping, lever arms,
   prediction output and every calibration column explicitly.
3. Compare the original arithmetic, each change separately, and both together.
   Use independent known-motion formulas and controls across all three physical
   candidates and both processing cases. Reject changes to the physical equations,
   active nuisance set, time support or input arrays.

These are diagnostic alternatives, not a replacement production method.

## Then compare the same four points

Only after software qualification, prepare a new source/environment/input freeze
using the same four already exposed examples as the completed stopping study.
Reconstruct and verify the original arrays, parameter order, error operator and
baseline cost. Preserve all failed labels.

For each point and each of the four arithmetic settings, retain the full
Jacobian and compare the timing and gyro-Z-offset columns with the same three
finite-difference step sizes. Record branch membership and signed errors.
Do not optimize, forecast against new observations, or introduce new noise seeds.

Freeze at most **16 residual-and-Jacobian evaluations per setting**: at most
256 across the four points. Error-operator reconstruction needs its own charged
allowance, separate from these evaluations. Its frozen upper bound is 23,634
single-packet reconstruction operations per point (23,555 supported packets
plus 79 query operations). With 64 complete evaluations, each task is limited
to **23,698 native calls and 119,117,714 conservatively counted packet-query
visits**. Across four points the caps are 94,792 calls and 476,470,856 visits.
Unused prepaid work stays charged; these are new allowances.

Use at
most two workers with one numerical thread each, and a one-hour cooperative
ceiling. Each worker allows three compiler builds: the original noise bridge,
original wider tangent and separate boundary-branch tangent. Relative longitude
wraps the supplied kernel and requires no extra compilation. No retries.

## Shared implementation

`lll.ilvis0_timing_arithmetic` provides the diagnostic kernels and coordinate
wrapper; `lll.timing_arithmetic_probe` owns the fixed differences and charges.
`lll.timing_arithmetic_study` uses the study engine and binds only the probe
dependency of the original reconstruction function. `lll.timing_arithmetic_report`
packages sealed outputs without refitting. No worker or library tree is copied.

The physical and numerical sources from the original calibration remain
unchanged. Two framework files retain their intervening CI repairs: archive
pack/lookup handling and test socket preflight. Record their old and new hashes
explicitly; they do not change equations, observations or the error operator.
Require the original numerical environment to match exactly.

## Finish line

Publish a matched table showing which discrepancy each change removes, what
remains, all failed controls and the complete charged work. Stop this phase at
that report, even if neither alternative helps. A later solver qualification or
fresh calibration needs a separate finite plan; no acceptance limit is relaxed.

[Roadmap](ANALYSIS_ROADMAP.md) · [Next analyses](NEXT_STEPS.md).

# Selective-precision arithmetic: long-record check

The new isolated prototype keeps wider precision for the ten parameter
sensitivities that missed the tolerance in the previous long-record benchmark.
Its other seventeen derivative directions use ordinary precision. The
physical-value calculation and output interface still follow the unchanged
wide reference.

The initial six generated two-second cases passed bitwise position and
residual checks, timing-boundary checks, and every 26/27-column derivative
comparison. The separate frozen twenty-minute study has now completed all six
physical-candidate/processing-setting combinations. Its saved arrays show
**zero derivative tolerance violations**, bitwise-identical positions and
residuals, and correct timing boundaries. All 12 native calls and all six
construction journals verify against their charged limits. No optimizer was
started and no observed or protected recording was read.

On these generated native calls, the selective version ran 2.03–2.21× faster
than the unchanged wide reference. That is a kernel measurement, not a
whole-fit speed measurement. The [separate two-minute paired fitting and
prediction study](paired-qualification/README.md) passes all six generated
cases. The [twenty-minute paired study](long-fit-study/README.md) also passes
all six: both variants converge and meet the prediction screen, and their
largest matched forecast difference is 1.63 × 10⁻⁹ m. A [separate whole-fit
timing study](timed-fit-study/README.md) repeated all six cases and measured
2.38× median fit CPU speedup, with every case faster. The first long-fit
release stopped on an adapter import before charging a case; its failure is
preserved. The earlier all-ordinary derivative prototype still fails its
long-record tolerance check. A [same-source paired ESA check](../esa-observed-hybrid/PLAN.md)
finished with [21 of 24 pairs passing](../esa-observed-hybrid/combined/README.md),
so the faster method is **not qualified** for observed-data replacement.
At six saved failed-fit points, the values match exactly but the derivative
columns differ by up to about one micrometre per normalized parameter unit.
A separate revised prototype widens the two attitude columns with the largest
differences. Source generation and a six-case, two-second generated physical
comparison now pass: values and differences match the wide method bitwise,
and all derivative columns meet the fixed local tolerance. This short control
does not qualify substitution in the 20-minute observed fits.
The [six saved-point ESA check](../esa-observed-hybrid/same-point-v2/README.md)
also passes its predeclared improvement gate at every point: position values
and timing boundaries remain identical, while the largest derivative difference
is at least ten times smaller than before. No model was refitted, so the
original 21/24 observed substitution result remains unchanged.
The established wide method remains in use. These checks make no Earth-model
decision.

The subsequent [three-pair observed development run](../esa-observed-hybrid/three-pair-v2/WALL_CAP.md)
reached its frozen four-hour wall cap. All three tasks sealed as budget
failures after 349 native calls. Their wide fit and forecast artifacts are
preserved, but no revised fit or paired comparison completed. This leaves the
faster method unqualified; the unfinished-task recovery route does not apply.

[Frozen plan](PLAN.md) · [Sealed long-record evidence](long-study/README.md) ·
[Paired fitting evidence](paired-qualification/README.md) ·
[Long paired fitting evidence](long-fit-study/README.md) ·
[Whole-fit timing](timed-fit-study/README.md) ·
[Earlier failure diagnosis](../mixed-tangent-long-controls/DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

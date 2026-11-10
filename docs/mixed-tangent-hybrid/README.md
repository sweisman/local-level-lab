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
prediction study](paired-qualification/README.md) now passes all six generated
cases. Both variants converge and meet the prediction screen; their largest
forecast difference is 1.40 × 10⁻⁹ m. The earlier all-ordinary derivative
prototype still fails its own long-record tolerance check; its frozen result
is unchanged. A long-record fitting comparison remains before replacing the
current fitter. These checks make no Earth-model decision.

[Frozen plan](PLAN.md) · [Sealed long-record evidence](long-study/README.md) ·
[Paired fitting evidence](paired-qualification/README.md) ·
[Earlier failure diagnosis](../mixed-tangent-long-controls/DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

# Long-record paired fitting check

The six generated twenty-minute cases passed the predeclared comparison between the existing wide-precision tangent and the selective-precision tangent. The cases cover all three physical candidates and both processing settings. Each pair used the same generated measurements, training split, initial values, optimizer, bounds and 1,199 withheld receiver positions; only tangent arithmetic changed.

Both fits in every pair converged, retained the nuisance directions and passed the existing physical prediction screen. Across 7,194 matched forecast positions, the largest three-dimensional difference was **1.63 × 10⁻⁹ m**, below the fixed 0.01 m tolerance. The largest training-cost difference was **1.63 × 10⁻¹⁵**. The worker charged 136 native calls and 28,913,633,028 packet/query visits, with no errors, in 68.3 minutes. An independent replay of the sealed results qualified all six cases and verified the source, inputs, charges and saved comparisons.

The first release stopped before any case was charged because its frozen adapter could not be loaded outside the package context. Its terminal failure remains preserved. The corrected release changed the adapter import and added a direct-load software test; it kept the scientific design and limits.

This qualifies numerical agreement of the two tested fitting paths on these generated long records. The earlier native-call benchmark found a 2.03–2.21× speedup for the selective tangent, but this study did not independently measure whole-fit CPU time by variant. Replacement in observed-aircraft fitting still requires that measurement and a separate source-bound observed-data release. The study used no observed or protected recordings and made no Earth-model decision.

[Frozen plan](../LONG_FIT_PLAN.md) · [Short fitting check](../paired-qualification/README.md) · [Roadmap](../../ANALYSIS_ROADMAP.md).

# Independent bounded searches reach the same noisy turning costs

The [finite comparison](TURNING_NOISY_SOLVER_PLAN.md) completed four technical
tasks: SciPy trust-region reflective and dogbox methods at each of the two
sealed generated turning points. It used the original noisy training inputs,
26 nuisance parameters, bounds, clock and objective. No observed or protected
recording was opened. The original failed fits remain unchanged.

| Original case | Independent method | SciPy stopped successfully? | Cost improvement over original | Original full stopping check? |
| --- | --- | --- | ---: | --- |
| Turning, level | Trust-region reflective | Yes | 2.85 × 10⁻¹⁰ | **Failed** |
| Turning, level | Dogbox | Yes | 5.74 × 10⁻¹² | **Failed** |
| Turning, shallow climb | Trust-region reflective | Yes | 1.46 × 10⁻⁹ | **Failed** |
| Turning, shallow climb | Dogbox | Yes | 1.70 × 10⁻¹¹ | **Failed** |

The original costs are about 213.73 and 213.76, so none of these reductions
is a meaningful change in model fit. At all four new points, the projected
stationarity and physical-position parts of the original check pass. Its
fresh full-correction relative cost change is still about 1.63 × 10⁻⁷ for
the level route and 0.89 × 10⁻⁷ for the shallow climb, above the required
1 × 10⁻⁸. SciPy's own successful termination is **not** the project's
convergence gate.

Together with the [exact-target control](TURNING_KNOWN_OPTIMUM_RESULT.md),
this narrows the numerical problem: the solver can fit a constructed exact
turning target, while three bounded methods reach essentially the same cost
near the noisy turning minimum and fail the same full-correction criterion.
These finite searches do not prove a global optimum. The next step is to
qualify a separately versioned stopping rule against known minima,
nonstationary and poorly identified controls. Any revised rule must apply
equally to all physical candidates before a larger motion or aircraft study.
No model decision or aircraft error-law coverage follows here.

The sealed study is `data/generated-turning-noisy-solver-v1-20261117`.
It retains each native operator binding, full evaluation trace, SciPy result,
original stopping components, source/input hashes and charged work.

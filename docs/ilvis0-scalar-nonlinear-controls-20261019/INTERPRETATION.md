# Bounded calibration: what passed and what remains

The study completed its full frozen allowance of **228 mathematical starts**
using **40,236 residual/Jacobian calls** in 14.39 seconds. There were no observed
fits, original-file reads or native integrations. Every failure is preserved;
the study will not restart or spend its unused allowance.

## Known solutions passed; the full matrix did not qualify

All **12 known-answer starts passed**, including exact-boundary, near-boundary,
interior and rank-deficient controls. Analytic derivative and fresh endpoint
checks passed their unit tests before the freeze.

In the matched constructed-history matrix, **136/216 endpoints passed**, but
only **32/72 three-start comparisons** passed every required check:

| Constructed motion | Complete comparisons | Out of |
|---|---:|---:|
| Stationary | 0 | 18 |
| Eastbound | 0 | 18 |
| Changing direction | 17 | 18 |
| Climbing | 15 | 18 |

All 80 unsuccessful endpoints exhausted the 200-evaluation allowance. Their
residual RMS values were approximately 1.15 × 10⁻¹⁰ to 3.50 × 10⁻⁷ m/s².
Most failures therefore occur where almost nothing remains to fit, not where
a physical candidate visibly misses the constructed force magnitude.

Of those 80 budget failures, 53 satisfy the separately saved fresh stationarity
limit. They **remain failures**: the frozen rule also requires solver completion.
Saved diagnostics do not retroactively replace that rule. The other 27 failures
also miss the fresh stationarity limit. Successful optimization cannot be
inferred merely from a small scalar residual.

## Changing motion can preserve a scalar difference

All 24 wrong-model changing-direction/climbing comparisons passed their
three-start checks. Wrong-model RMS spans about 0.00551–0.0131 m/s² in the
direction-changing controls and 0.000137–0.00215 m/s² in the climbing controls.
These are feasible finite numerical comparisons, not globally certified optima,
noise-normalized evidence or results from the aircraft archive.

The separate exact constant-gain construction already demonstrates straight-leg
ambiguity. The zero complete-comparison counts above do not create a new
stationary/eastbound model finding; they show that this numerical method is not
qualified across both informative and nearly uninformative inputs.

## Consequence for the roadmap

**C02 remains open; C04 observed channel fitting is blocked.** A follow-up needs
a separately identified candidate that handles near-zero residuals and flat
calibration directions honestly, with unchanged bounds and repeat acceptance.
No larger observed budget, relaxed stopping check or retry of this study follows.

Independent C03 quantization/timing controls and metadata work may continue.
The main result stays **53 globe / zero flat / zero unresolved**; the separate
IMU21 horizontal-only sensitivity remains unresolved. None of these mathematical
controls changes an airborne disposition.

[Every start](starts.csv) · [Completed report](README.md) · [Frozen scope](PLAN.md) ·
[Authoritative backlog](../ANALYSIS_ROADMAP.md).

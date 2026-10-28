# Two-sided timing diagnostic at saved points

## Question

Do the failed stability corrections cross a genuine change of slope in the
physical calculation, or are their cost changes explained by other nonlinear
calibration directions or inaccurate derivatives?

The [saved linear replays](prediction-linear-timing-review/README.md) identify
boundary crossings in both failures and neither matched control. The
[analytical controls](timing-kink-controls/README.md) show how a smooth-step
check can reject exact nonsmooth minima. Neither result establishes the cause
in the physical calculation.

## Inputs and unchanged calculation

Use only four already exposed generated-data points from the closed fresh
calibration: seeds 281474977010692 and 281474977010693, rate-sample errors,
specified-field globe with removal allowed, starts 0 and 1. Preserve original
labels, every nuisance column and every failure.

Reconstruct exactly those existing inputs with the frozen generator. Verify
all stored array hashes, training observations and error-operator bindings.
Use the same compensated mean, noise propagation, numerical environment,
gravity anchor, physical bounds and training-only receiver rows. Never call
the fitter or produce a new forecast. No new seed families or aircraft reads.

## Measurements at each point

1. Replay the saved residual, complete 27-column Jacobian and cost, then repeat
   them to check exact reproducibility.
2. Evaluate the saved full correction, timing alone and all other coordinates
   with timing held fixed. Compare actual and linearized cost changes.
3. Locate the nearest common integration boundary from the verified clock.
   Record its cost, without treating its slope as a smooth derivative.
4. At 10, 1 and 0.1 microseconds on each feasible side, compare the analytical
   timing column with a centered difference wholly inside that interval. Each
   difference uses a quarter of that side's boundary distance. Preserve the
   existing comparison scale `1e-8 + 1e-6 * max(column norms)`.

Both sides are required at the failed interior points. A side beyond a physical
bound is recorded as infeasible, never evaluated. Probe locations may be clamped
to a physical bound only for normalized roundoff within `1e-10`; original saved
points and observations are unchanged. Full Jacobians remain in every report.

## Separate finite allowance

Four tasks, four workers, one numerical thread each, no competing numerical
jobs. Maximum 64 complete residual/Jacobian evaluations per point, 256 total;
the declared sequence needs at most 24 per point. Cooperative wall ceiling:
one hour. Expected execution is roughly 5–15 minutes, not guaranteed.

The shared reconstruction allowance gives each task at most 23,698 native
calls and 119,117,714 packet visits, including reconstruction. Total ceilings:
94,792 calls and 476,470,856 packet visits. Charge before execution; preserve
interruption, failure and unused charges. No retries or allowance expansion.
Compilation is limited to two source-bound kernels per worker.

## Implementation and qualification

Add small `lll.timing_boundary_probe`, `lll.timing_boundary_study` and
`lll.timing_boundary_report` components. Reuse the existing saved-point capture,
compensated kernel provider, journals, `lll.studies` lifecycle and archive.
Do not copy a worker or change the scientific kernel.

Before execution, qualify independent smooth/kink references, both timing
branches, physical bounds, full-column preservation, charging, exact replay,
source/environment/selection guards and capture before fitting or forecasting.
Freeze the qualified sources, environment, four inputs and this allowance.

Publish all results and derivative curves, including disagreements. This is a
diagnostic, not a new convergence decision, solver qualification, uncertainty
threshold or Earth-model vote. Calibration and validation remain blocked.
Any revised solver or further campaign requires its separately reviewed phase.

[Next analyses](NEXT_STEPS.md) · [Roadmap](ANALYSIS_ROADMAP.md).

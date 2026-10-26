# Next bounded phase: explain the stopping failure

**Approved bounded phase.** This phase investigates the two failed calibration
fits without refitting them or launching another calibration campaign.

Both fits passed the position-error screens. Their fresh-check position changes
were under 0.5 mm, but their relative cost change exceeded the numerical limit.
Before replacing the solver, determine whether this comes from its derivatives,
numerical repeatability or the step used to check convergence.

## What would run

| Step | Fixed work | Cooperative limit |
|---|---|---:|
| Check the diagnostic software | Twelve known-answer problems and sixteen guard cases | 30 minutes |
| Examine saved parameter values | Four fixed-point numerical probes; no new nonlinear fits | 2 hours |
| Audit and publish | Error tables, interpretation and remaining limits | 30 minutes |

The phase ends with its report, including an inconclusive or failed outcome.
It does not automatically proceed to a new solver or another campaign.

## The four points

Use the two failed starts, one successful start from the preceding noise example,
and one successful alternate-processing start from the failing example. All
four are already exposed development examples using simulated measurements;
reserved validation seeds and aircraft recordings remain untouched.

At each saved point:

1. Repeat the same residual calculation three times to check repeatability.
2. Compare every analytic derivative with finite differences at three fixed
   step sizes, respecting parameter bounds.
3. Repeat the original undamped stopping probe and separate its cost,
   stationarity and position checks.

These measurements can identify inconsistent derivatives, limited numerical
precision, or a difficulty in the local step. Agreement would narrow the
problem but would not prove that the original fits reached an optimum.

## Firm limits

- **Zero new nonlinear fitting starts.** The original failed labels stay failed.
- Four numerical tasks, at most 170 residual/tangent evaluations per point.
- At most 239,816 prepaid native calls and 1,506,051,012 packet-query visits,
  including reconstruction of the unchanged input-error operator.
- At most two workers, one numerical thread each; reserve two threads while
  the older test run owns them. No process is terminated to enforce a deadline.
- Keep every nuisance coordinate and the original cost, stationarity and
  position tolerances. No threshold changes, retries or extra examples.

**Finish line: a verified report within a three-hour cooperative execution
allowance, then stop for review.** No statistical confidence or Earth-model
decision is produced by this diagnostic.

[Previous phase outcome](PREDICTION_PHASE_RESULTS.md) ·
[Implementation and exact selection](prediction-stopping-consistency/IMPLEMENTATION.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).

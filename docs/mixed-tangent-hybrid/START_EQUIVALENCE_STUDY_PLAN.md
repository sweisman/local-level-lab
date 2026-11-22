# Generated two-start method qualification

## Question

Can the faster model-declared tangent and the established wide tangent give
equivalent forecasts when their training optimizers choose different, nearly
tied starts? This is a **new software-method study**. The original observed
5/8 exact-start result remains failed and no Earth-model decision is made.

## Frozen design before a new outcome

- Use the existing 120-second generated aircraft protocol, 55° latitude,
  three physical candidates and both upstream-removal settings. Evaluate
  **two fixed starts per setting**: 12 paired tasks and 24 fits. The same
  generated IMU/receiver history must be bound across the two starts and
  both tangent methods within each setting. Never choose a start using later
  receiver positions.
- The wide tangent is the reference in all tasks. The candidate uses the
  model-declared selective tangent for globe and the same wide tangent for
  the disc. Retain the original 0.01 m matched-forecast target. Set the
  near-tie cost tolerance to **1e-8 relative**, the existing fit cost-change
  threshold. It is not chosen from the saved observed cost gaps.
- Require each fit to pass its original numerical and physical checks and
  retain every nuisance column. Require every same-start method comparison
  to pass the 0.01 m target. Then apply the
  [start-equivalence method](START_EQUIVALENCE_METHOD.md) to **all starts**
  within each of the six settings. A method qualifies on this generated
  matrix only if all six settings pass. Save every fit, failure, training
  cost, forecast and input/time binding.
- Maximum **402 native calls** and **752,906,000 packet/query visits** per
  paired task, hence 4,824 calls and 9,034,872,000 visits across the study.
  Declare four workers at one numerical thread each, a one-hour cooperative
  wall allowance, and finite construction charges at the existing paired
  task limits. These are ceilings; the prior six-pair study used 120 native
  calls and about 6.5 minutes, so this matrix is expected to be much smaller
  than its allowance.
- Before launch, freeze exact source, generated recipe, parent receipts,
  environment, six case identities with both starts, limits and success
  rule. Pass source-bound tests and a finite reboot/worker-interruption
  recovery test. Reuse sealed completed outcomes; never retry a completed
  numerical failure. No original NASA/ESA file or protected group is read.

## Interpretation

Passing would qualify this two-start **generated** method check only. It
cannot revise the original exact-start failure or authorize observed
substitution. A separately selected ESA development input must then test
the revised frozen rule, with all fits and failures preserved. Any failed
generated setting blocks that dependent observed comparison; diagnose its
saved results without changing this study's allowance or limits.

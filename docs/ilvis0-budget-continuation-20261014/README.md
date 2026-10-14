# Continuation of three budget-limited comparisons

The completed precision recovery raised the findings to **41 globe preferences,
zero flat and 12 unresolved**. Three of those unfinished stretches each have one
primary model fit that exhausted its forty-evaluation allowance. The other five
primary fits and the original scheduled repeat passed in each stretch.

This separate study continues those three failed endpoints with **up to 200
evaluations each**. Each continued fit also receives its own perturbed-start
repeat. Two completed recordings supply fresh controls. The fifteen passing
parent primaries are reused with their original hashes; their costs are not chosen
by searching earlier attempts. The original failures remain preserved.

The [finite plan](PLAN.md) permits **eight new starts and 1,296 native sweeps**,
with no retries and four total numerical threads. Measurements, complete selected
intervals, physical models, calibration bounds, receiver weights, integration
clock and stopping tolerances remain unchanged.

Every positive comparison needs all six primary fits, its new targeted repeat and
both controls. The new freeze is separate from the completed 86-start study; none
of that study's unused allowance is spent again. Predictions and fits are charged
before execution and saved atomically with hashes and exclusive locks.

After this stage finishes with passing controls, the same worker proceeds to the
[nine remaining stretches](../ilvis0-remaining-precision-20261014/README.md), using
their separately frozen scope and allowances. If a control fails, the sequence
stops before launching that stage. Results are packaged after each stage.

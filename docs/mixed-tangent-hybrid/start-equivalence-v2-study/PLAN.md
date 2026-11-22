# Fresh 180-second start-equivalence qualification

## Question and boundary

Test whether the model-declared tangent and established wide tangent return
the same useful forecast under the revised near-zero start rule on a **new
generated training geometry**. The completed 120-second study remains failed
under its frozen rule. No recorded NASA/ESA measurement or reserved flight
group enters this study, and passing cannot authorize observed-aircraft
substitution by itself.

## Frozen case and rule

- Use the existing generated `fast` route at 55° latitude for **180 seconds**
  and 179 receiver queries; the old study used 120 seconds and 119 queries.
  The new training split and later path include generated times absent from
  the original study. Keep its three models, both upstream-removal settings,
  two fixed starts, calibration bounds, noise policy, 300 Hz IMU rate and
  common input binding. There are 12 paired tasks and 24 fits.
- Use the wide tangent as reference. Use model-declared selective tangent
  for globe and wide tangent for disc. Keep the 0.01 m maximum forecast
  separation. Compare costs with the existing `1e-8` relative tolerance and
  an absolute floor of `1e-8` sum-of-squares units, exactly the pre-existing
  near-zero solver acceptance ceiling. Require every fit to pass its own
  numerical and physical checks, same-start costs to agree, any changed
  primary start to be near-minimal under both methods, and all near-minimum
  forecasts to agree both **across** and **within** methods. Later receiver
  truth never selects a start.
- A setting passes only if both starts and all these rules pass. The generated
  method gate passes only if all six settings pass. A failed setting blocks
  dependent observed substitution; preserve it without changing this rule.

## Finite execution and recovery

Each task has at most **402 native calls** and **1,711,750,000 packet/query
visits**, totaling **4,824 calls** and **20,541,000,000 visits** across 12
tasks. Declare four workers at one numerical thread each and a two-hour
cooperative wall allowance. Use a fresh study identity, source/environment
qualification, exact parent receipts, charged starts, append-only journals,
atomic outputs and task-level resume. Prove interruption recovery before
launch. Completed failures are never retried. Keep historical source bytes
unchanged; the new adapter calls shared calculation components.

If the generated gate passes, separately freeze an observed development
comparison with its own objective-scale rule and finite allowance. The
absolute cost floor above belongs to the generated near-zero stopping
policy; do not transfer it to aircraft fits without justification.

# Native turning-route solver control with known optima

## Question

Can the existing bounded solver recover a known zero-cost path on the same
generated turning-route training problem that stopped in the four-case motion
control? This is a **numerical** control. It cannot validate the aircraft
motion model, receiver covariance or an Earth-model decision.

## Construction

Reconstruct the two sealed turning training problems from their generated
recipe, with the same input noise, receiver reports, bounds, clock, covariance
and all 26 nuisance columns. Verify their array hashes and training operator
against the sealed parent. At each parent's saved feasible point, evaluate the
native residual once. Define a shifted control residual as the native residual
at a trial point minus that saved target residual. The Jacobian remains the
native Jacobian. The target point therefore has exact zero residual by
construction, while the route geometry and nonlinear parameter response stay
in the native pipeline. This target construction is a solver test, not an
independent synthetic aircraft truth.

Use two declared starts per route: the original zero point and a deterministic
interior perturbation from the known target. For each of the four tasks, fit
with the unchanged bounded solver and stopping rule, at most 80 evaluations.
Score objective recovery, predicted observation agreement with the known
target, numerical convergence, bound feasibility and total charged work.
Parameter equality is not required where the nuisance space is unidentifiable.
No original recording or protected ESA group is read, and no prior failed fit
is relabeled or retried.

## Limits and gate

Four tasks, two one-thread workers, 20-minute cooperative wall limit. Every
native call and packet visit is prepaid before execution. Source, environment,
selection, target construction, starts, finite allowance and generic task
recovery are qualified and frozen before launch. Reboot continuation schedules
only unfinished tasks under their original charges. A completed failure stays
failed. This control qualifies the solver for the constructed zero-cost
problem only if all four tasks converge, reproduce the target path to the
predeclared 1 mm maximum physical difference and reach relative residual
cost below 10⁻⁸. Passing still would not qualify the original noisy turning
optima; that requires a separate bounded comparison if needed.

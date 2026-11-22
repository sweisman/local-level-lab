# Base-bounds correction for the ESA local-uncertainty task

The [second task](LINEAR_UNCERTAINTY_V2_RESULT.md) stopped before native
forecast because its adapter supplied the wrong bounds-object type. Its
terminal result and full charge remain unchanged. This new identity keeps
all scientific inputs, model, fit, split, error law and source data from
the [corrected derivative plan](LINEAR_UNCERTAINTY_V2_PLAN.md).

Construct the native forecast problem with the original base `Bounds`, which
its constructor requires. A focused local test must exercise that constructor
before launch. The full operator is built once, its early cost and determinant
must replay, and one fitted-point native forecast supplies the missing
Jacobian. The same 0.1 mm position replay, `1e-6` relative and `1e-8`
absolute whitened-Jacobian replay, all-column rank check and bound gate apply.

One start, one thread, one hour, 450,000 native calls and one billion packet
visits. No later receiver value or reserved ESA group enters the worker.
An estimable, in-bounds covariance is only a local linear diagnostic; the
scientific decision remains abstain.

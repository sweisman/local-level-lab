# Typed 51-column joint prediction qualification

The new native candidate passes all 24 matched controls. Qualify its separate
training/prediction interface before a complete generated comparison. Retain
all 27 physical and 24 auxiliary columns, one shared unknown vector across
epochs, the original calibration boxes and exact support certificates.

Freeze 36 software controls: twelve known-answer affine systems spanning three
axes, two expansion centres and two noise allowances; nine force-only systems
exercising every new matrix-error column; and fifteen negative controls.
Negative controls cover source, time, centre, both physical domain endpoints,
all three coefficient bindings, force-source consistency, clock/matrix binding,
combined reference binding, inconsistent training sources and attempted future
observation input. No future receiver value is accepted by the prediction API.

Known future radii must equal the declared nonlinear allowance plus three times
the training noise within 1e-12, while retaining all 51 columns. Reject every
deliberate mismatch before support optimization. Reserve six LP proposals and
twelve exact certificates per positive identity; reserve zero for each negative
identity. Totals: 36 starts, at most 126 proposals and 252 certificates.

Four workers use one numerical thread each, with 120 cooperative seconds and
one second per LP proposal. No native integration calls, native bounds,
original aircraft reads, fits, retries, extensions or process signals.
These are provided-bound affine software controls, not physical aircraft
simulations or observational coverage. Only full qualification permits a
separately frozen complete native prediction comparison.

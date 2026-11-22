# Generated solver forecast qualification

## Question

Do two bounded solvers, started differently, produce the same withheld path
after fitting only earlier receiver positions? This is a software control for
the numerical stopping problem in the twenty-group retrospective study. It
does not reclassify those fits or estimate aircraft prediction coverage.

## Inputs and finite design

Reuse the six independently generated 12-second geographic controls: each
of the three physical candidates under a constant or known varying packet
period. Keep their analytic IMU and receiver truth generator separate from
the navigation predictor. Fit only the first 16 of 24 receiver epochs;
forecast the remaining eight without giving their positions to either
solver. Use the same six calibration parameters and bounds as the earlier
geographic control. Include both zero and opposed starts for the original
and verified-stop bounded solvers: 24 task identities. The controls contain
interior and near-boundary calibration settings.

Freeze source, C/C++ kernels, Python/NumPy/SciPy environment, exact task
grid and this plan before any fit. Allow at most 200 native tangent sweeps
plus two value predictions per task, with one charged task start and no
scientific retries. Use at most four total numerical threads. Qualify
hash-verified task-level recovery before launch; an interrupted task may
resume under separately charged unchanged limits. Preserve every failure.

## Checks and interpretation

For each task save the training fit, known-answer training objective and
complete forecast path. Score the later eight receiver positions only after
the path is saved. Report numerical stopping, objective difference,
later-path error against independently generated truth, and path differences
between methods and starts. A successful software gate requires every task
to stop, reach training cost within 0.01 of the known-parameter cost, and
keep later-path differences within 0.1 m for the same generated fixture.
The 0.1 m threshold is a software consistency tolerance, not aircraft
measurement accuracy.

A failed gate remains a failed result. Passing would qualify only these
short, six-parameter generated controls; full 26-parameter aircraft fits,
observed stopping changes and absolute prediction-error coverage remain
separate gates.

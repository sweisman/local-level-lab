# What the fresh probes established

All twelve saved centers reproduced bit-for-bit, including both residuals and
their parameter derivatives. This checks that the diagnosis uses the same
generated observations, clocks, model configurations and parameter order as the
failed full-calibration qualification.

The original probe again fails on all four flat-model endpoints. Its actual
cost rises to roughly 1e-7, and fresh stationarity rises above 1e-4. The
column-scaled ridge proposals pass the same local numerical limits on all
twelve endpoints, including those four. Their flat-model costs stay near 1e-14,
with fresh stationarity near 1e-11.

This supports the specific diagnosis: a correction chosen from an ill-conditioned
linear approximation can travel too far through weak parameter directions even
when the endpoint already fits the scored observations extremely closely.
Penalizing correction displacement can avoid that move while retaining every
parameter column. The penalty is not part of the physical-model score.

These are fixed-point checks, not completed fits. They do not resolve the
zero-field globe's paired objective difference. A separate staged qualification
must demonstrate both successful final checks and repeatability from the
predeclared starts. The earlier failed qualification remains failed.

The saved native probe artifacts contain the scored horizontal residuals and
derivatives. They do not preserve fresh probe heights, although the plan requested
unscored-coordinate errors. Endpoint height errors remain in the parent outputs;
no omitted-height stability claim follows from these checks. The staged fitting
study preserves all three predicted coordinates at each returned endpoint.

[Fixed-point results](README.md) · [Staged qualification scope](../ilvis0-horizontal-ridge-qualification-20261018/PLAN.md).

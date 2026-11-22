# Versioned observed optimizer comparison

This study uses the same three preselected NASA development recordings, two
time cuts, two fixed starts, rotating-globe observation model and calibration
bounds as the earlier [pilot plan](OBSERVED_METHOD_PILOT_PLAN.md). It compares
the custom bounded trust-region optimizer with independent SciPy TRF: **24
fits**. All original 80 fit outcomes remain unchanged.

The earlier pilot was prepared but never charged. A repair to the shared
recovery launcher changed a source bound by that preparation. This version
freezes the repaired recovery source under a new identity. It reuses the old
scientific task/evaluator definitions and adds no nuisance terms.

Before preparing any observed fit, require a passing 24-fit, six-fixture
[long generated comparison](LONG_INDEPENDENT_SOLVER_PLAN.md), including its
sealed task continuation after the host interruption. Then qualify a separate
one-task SciPy real-worker preflight. Freeze the selected input bytes, source
and numerical environment, four one-thread workers, per-task native-call and
packet-visit caps, and a cooperative six-hour wall allowance. Prepay native
work and preserve every failure. Reboot recovery may assign unfinished
identities to separately charged finite stages; it may never repeat a sealed
result.

Compare the two methods on matched earlier-only training data and predict
later receiver reports without using them in fitting. Report convergence,
path agreement, cost, per-axis later-position errors and physical adequacy
separately. This is development evidence, not calibrated detection or
independent validation. Protected ESA confirmation recordings remain closed.

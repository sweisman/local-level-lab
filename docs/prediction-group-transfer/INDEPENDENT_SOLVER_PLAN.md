# Independent bounded-optimizer control

The [scope correction](SOLVER_INDEPENDENCE_ERRATUM.md) found that the two
providers in the earlier generated checks share one optimizer. This finite
software study compares that trust-region optimizer with a separate SciPy
bounded `trf` implementation on identical generated observations.

Preselect six 60-second histories: all three physical candidates under
both exact-grid clock policies, 300 Hz header-elapsed and 200 Hz nominal.
Put Z-gyro calibration near its permitted boundary and give each history
a distinct increment-noise seed. Fit the first 39 of 59 receiver reports;
save the complete forecast before scoring the final 20. Run the trust-region
and SciPy `trf` methods from zero and fixed perturbed starts: **24 tasks**.

First run a separately frozen, 10-second one-task **SciPy** real-worker
preflight. Freeze source and native hashes, the six recipes and seeds,
numerical environment, four one-thread workers, per-task native-call and
packet-visit caps, cooperative wall cap and task-level reboot recovery.
The SciPy adapter must use the common counted training proxy so every
native evaluation is charged once. Preserve failures; do not alter completed
generated studies, aircraft fits or protected confirmation inputs.

The numerical gate requires all 24 fits to pass the unchanged final
stationarity and fresh stability checks, all four within-fixture forecasts
to remain within **0.1 m** on the withheld period, and four training costs
within **0.01** of one another. Report generated physical error separately.
If the gate fails, keep the result and diagnose the disagreement before
any observed-method change. A pass would qualify these generated cases,
not aircraft predictive coverage, a global optimum or an Earth-model
detection. A longer independent-method confirmation would then be needed
before an observed development comparison.

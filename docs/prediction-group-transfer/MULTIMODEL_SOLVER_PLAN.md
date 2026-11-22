# Multimodel full-calibration solver forecast control

The [first full-calibration pilot](FULL_CALIBRATION_SOLVER_RESULT.md) passed
four fits on one generated specified-field globe flight. This next software
study asks whether the same numerical agreement survives all three physical
candidates and calibration settings near the Z-gyro boundary.

Generate six independent 60-second, 300 Hz histories: rotating globe,
zero-field globe and stationary disc, each with interior or near-boundary
Z-gyro calibration. Use the existing independent aircraft/IMU generator,
one fixed increment-error law and a fixed noise seed. For each history,
fit only the first 39 of 59 receiver reports and forecast the final 20.
Keep all 26 nuisance directions, the same physical bounds, header-elapsed
clock and declared processing assumption. Compare the near-zero and trust
region bounded solvers from zero and fixed perturbed starts: **24 tasks**.

First run a separately frozen, 10-second, one-task real-worker preflight.
Freeze sources including native kernels, numerical environment, recipes,
task identities, the finite per-task call and packet-visit limits, and
task-level reboot recovery. Reserve at most four total numerical threads.
Charge work before execution; preserve every failed or interrupted task.
Do not read observed aircraft or reserved confirmation data.

For each fixture report all four numerical stopping results, training costs,
physical errors against withheld generated truth, and maximum pairwise
forecast-path separation. The study is a diagnostic. A complete numerical
agreement gate requires all 24 fits to stop and all six four-fit paths to
agree within 0.1 m; physical adequacy is reported separately and may fail.
No result changes the sealed 20-group aircraft fit labels. A separate
200 Hz nominal-clock study and longer independent generated histories are
still required before a revised observed stopping rule can be proposed.

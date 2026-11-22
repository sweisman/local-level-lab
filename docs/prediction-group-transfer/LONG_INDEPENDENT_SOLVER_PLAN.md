# Longer independent-optimizer control

The short [independent-method control](INDEPENDENT_SOLVER_RESULT.md) passed on
60-second generated histories. This separate finite study tests whether that
agreement persists over longer histories before comparing methods on recorded
aircraft data. The earlier long control used two wrappers around one optimizer
and does not answer this question.

Preselect six 120-second generated histories: three physical candidates under
300 Hz header-elapsed and exact 200 Hz nominal clocks. Give each history a
distinct noise seed, place Z-gyro calibration near its allowed boundary, and
hold out the final 40 of 119 receiver reports. Fit the first 79 reports with
two genuinely separate bounded optimizers, SciPy TRF and the existing custom
trust-region solver, from zero and one fixed perturbed start: **24 tasks**.

First freeze and run a separate 10-second one-task SciPy real-worker preflight.
Freeze source and native hashes, recipes, numerical environment, four
one-thread workers, finite per-task native-call and packet-visit caps, a
cooperative wall cap, and task-level reboot recovery. Prepay native work.
Keep every failure and its charge. Use no recorded aircraft data or protected
ESA confirmation input in this control.

Pass only if all 24 fits pass the unchanged final stopping checks and, within
each generated history, all four withheld paths agree within **0.1 m** and
all four training costs agree within **0.01**. Report error against generated
truth separately. A pass qualifies this generated numerical control only; it
does not establish global optimality, aircraft predictive coverage, calibrated
uncertainty, or an Earth-model detection. Preserve all original aircraft fit
labels. If this gate fails, diagnose it before changing an observed method.

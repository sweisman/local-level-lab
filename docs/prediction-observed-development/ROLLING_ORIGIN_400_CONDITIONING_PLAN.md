# Earlier-origin conditional forecast

After both 400/120 fit tasks close, rebuild each passing fit's declared
receiver/IMU error operator over the same 520 prediction times. Use only
receiver reports 0–399 to condition that operator. Replay the exact saved
training cost and covariance log determinant before accepting a forecast.
The 120 later receiver positions must not be present in this study's inputs.

Use the already selected ESA development recording, specified-field globe,
header-elapsed clock, original calibration bounds, original fixed IMU error
law and saved fitted parameters. Run one fixed-law conditioning task for each
passing increment or point-rate fit; do no optimization and do not silently
replace a failed fit. Each task has at most 450,000 native calls and
1,000,000,000 packet visits, charged before execution. Reserve one numerical
thread per worker and no more than two workers, with a two-hour original wall
allowance. Qualify source, environment, prefix replay and reboot recovery
before launch. Preserve interruptions and numerical failures.

Save the uncorrected forecast, earlier-conditioned receiver mean and complete
future covariance *before* reading reports 400–519. Only after both tasks
close may a separate scorer open those positions. Report per-axis errors and
nominal interval coverage as development diagnostics. No calibrated coverage,
physical adequacy or Earth-model decision follows from this one recording.
The 120-report duration was selected after earlier outcomes were known, and
the seven reserved ESA groups remain closed.

# Identify the noise behind the generated forecast miss

The corrected six-case oracle study found large forecast errors even when it
supplied the generating fixed calibration and starting state. A separate
same-operator calculation found that the expected later horizontal error scale
is 717.66 m before receiver updates and 33.77 m after 800 updates. This study
asks which **realized input-error components** make the unconditioned forecast
miss in one preselected generated case.

Use only the rotating-globe, zero-removal, 55° latitude, 20-minute stream from
the sealed corrected oracle study. Regenerate the 300 Hz clean stream and the
same four independent error arrays from its frozen seed. Match the complete
noisy angle, velocity and timing arrays by SHA-256 to the original 24-case
generated parent and to the corrected oracle's selected stream before any
forecast. Supply the generating fixed calibration and initial state to every
variant. Keep all 1,200 query times and the later 400-epoch scoring interval.

Run ten fixed variants: clean; all four errors; each error alone; and all
errors except each one in turn. The four errors are gyro white increments,
gyro changing-bias increments, accelerometer white increments and
accelerometer changing-bias increments. Use the same draws in every variant.
Score every forecast against the same independently generated physical truth.
Report later horizontal and height RMS, maximum 3D error, and signed axis
errors. Compare the complete-noise variant to the already sealed oracle
forecast. Save the component array hashes and every forecast before exposing
the scoring truth. A component's leave-one-out effect is a counterfactual,
not a unique additive attribution; interactions must be reported explicitly.

Freeze one task per variant so sealed work survives a reboot. Allow one native
forecast call and 432,000,000 maximum packet-query visits per task, with no
optimization starts. Each task may construct 360,000 intervals and the exact
declared generated samples and random draws. Use at most two one-thread
workers, a two-hour cooperative wall ceiling, task-level recovery qualified
by an interruption test, and source/environment/input hashes. Never retry a
sealed technical or numerical failure. The same full-case comparison, not a
favorable score, is the technical gate.

This is generated-data error attribution. It makes no claim about real
aircraft noise, calibrated prediction coverage, or the shape or rotation of
Earth. Later observed-data work still requires an adequate receiver-error law.

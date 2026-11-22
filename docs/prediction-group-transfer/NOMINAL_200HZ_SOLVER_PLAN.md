# Generated nominal 200 Hz solver control

The [multimodel 300 Hz control](MULTIMODEL_SOLVER_RESULT.md) passed its
24 matched fits. This separate software study tests the archive's nominal
200 Hz integration path with all 26 calibration directions.

Generate six 60-second histories: three physical candidates, each with
interior or near-boundary Z-gyro calibration. Use a different declared
increment-noise seed for each history. Construct increments on an exact
200 Hz grid, with `dt = 0.005 s`, and fit under the `nominal_200Hz` clock.
The first 39 of 59 receiver reports may determine a fit; the final 20 are
withheld until its continuous forecast is saved. Compare both bounded
solvers from zero and fixed perturbed starts: **24 task identities**.

First qualify source, environment and reboot recovery, then run a separate
10-second, one-task real-worker preflight. Freeze the six recipes, source and
native hashes, numerical environment, four one-thread worker allocation,
finite per-task native-call and packet-visit limits, and cooperative wall cap.
Charge before work and retain failures. Do not read observed aircraft or
reserved confirmation data.

Report all 24 numerical stopping outcomes, six four-fit later-path spreads,
and withheld error against generated truth. The agreement gate requires all
24 stops and at most 0.1 m spread within each fixture. Report the generated
physical screen separately. An exact-grid nominal-clock result tests software
wiring and solver stability; it **cannot** measure sensitivity to irregular
packet-header timestamps. Longer generated histories and an explicit timing
perturbation control remain necessary before any observed stopping-rule
revision. The 50 original nonpassing aircraft fit labels remain unchanged.

# Finite execution qualification

Freeze the **19 named standard-library controls** in
`analysis/tests/test_ilvis0_control_shards.py`: eight storage/charge controls,
eight mocked process/status controls and three real-process lifecycle controls.
This tests execution machinery, not inertial observations or model fitting.

The three real-process controls each permit four child workers. They check
known JSON values, different completion order, independent process sessions,
inherited leases, a coordinator exception, rejection of a duplicate launch, and
continuation without repeating a charged identity. Every child explicitly
asserts that NumPy and SciPy were not imported. Other controls test changed
inputs/results, duplicate assignments, altered deadlines, interrupted charges,
incomplete transactions and cooperative failure stopping using constructed
fixtures. Deliberately corrupted copies are negative tests, not modified
scientific evidence.

Limits: **19 charged control starts**, **12 actual child-worker spawns**,
**120 cooperative seconds**, and at most **four worker slots with one thread
each**. Actual native integrations, original-file reads, observed fits and
protected ESA evaluations are all **zero**. Fixture ledgers contain simulated
native/bound reservations solely to test accounting; these are not IMU
calculations. Preserve every fixture and process log in the qualification output.
Charge controls and worker spawns before execution; no retries, expansions or
process signals. Any active children must finish normally before the next
control begins. Passing does not establish one-thread numerical compatibility;
the separate native qualification remains mandatory.

The qualification runs only after the current numerical allocation is free.
Freeze sources, test identities and environment before launch. A failure stops
remaining controls and remains visible. Rendering saved outcomes performs no
native work.

[Execution design](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

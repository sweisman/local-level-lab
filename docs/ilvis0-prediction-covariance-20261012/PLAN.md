# Frozen scope: receiver-correlation prediction comparison

Implement the [prepared method](../ilvis0-prediction-covariance-preparation-20261012/README.md)
without changing its measurements, cases, split or allowances. The immutable
proposal contains 12 identities: one October 5 recording, two shared covariance
assumptions, two processing cases and three physical candidates.

Maximum: 12 starts, 200 fit sweeps and 55 diagnostic sweeps per identity,
3,060 native sweeps total. No retries. Use one worker and two numerical threads.
Failed native calls and interrupted starts remain charged. A resumed worker
records an interrupted identity as unresolved and advances to unstarted identities.
It does not resume that identity's optimization or spend a second start.

Train on the first 292 receiver epochs and predict the remaining 147 continuously.
Retain all original IMU increments, header-elapsed timing, conversions and bounds.
Use training-only initialization and calibration. Apply the same full-stretch
covariance to every candidate; use its training marginal and full-stretch drift
anchor. Do not reset the path at receiver positions. Both covariance assumptions
remain reported; neither is selected by model preference or treated as calibrated.

Publish direct north/east/up errors, conditional receiver innovations, lag-one
dependence, nuisance parameters and limits, full-column rank and feasible nonlinear
axis probes. Fixed-zero removal has 26 active parameters; profiled removal has 27.
The center comes from one full-record tangent; every feasible ±0.01 normalized
axis step uses one value sweep. Record omitted outward steps and retain their
parameter columns. No probe reoptimizes nuisance parameters. Diagnostics do not
turn an unfinished fit into a converged fit.

The existing optimizer reserves its final tangent and two value diagnostics
inside the 200-sweep fit ceiling. Those value passes compare training-prefix and
full-record predictions, and check the training cost. The independent 55-sweep
diagnostic reserve cannot increase the optimizer allowance.

Preparation reads saved metadata and software sources. It copies expected original
hashes from the prior manifest without reading NASA originals. Launch verifies
those hashes, extraction provenance, the selected split, numerical environment
and native build. Any mismatch stops work; there is no silent new freeze.

An exclusive lock is inherited by a detached worker. Start and native-sweep
journals are flushed to disk before the action. Hashed atomic results preserve
failures. Completion seals summary and journal hashes. Publication checks those
hashes and reconciles each fit against its charges; packaging performs no fits.

Interpret shape before the specified-field/zero-field comparison. All scientific
decisions abstain. These retrospective sensitivities do not establish independent
confirmation, calibrated uncertainty, an absolute-fit acceptance threshold,
solar versus sidereal rate or the background field's cause.

September 24 replication and the full corpus are outside this allowance.

# Packet-aware timing solver qualification

The completed timing checks found a sharp change in the local time-alignment
derivative across an IMU packet boundary. This candidate rebuilds its local model
on each side before accepting a timing correction.

The [qualification plan](PLAN.md) fixes 67 known-answer software checks, including
piecewise timing examples and an explicit test that a genuine cusp cannot bypass
the original convergence gate. No archival measurements are fitted here.

Candidate: `analysis/lll/ilvis0_solver_timing.py`.
The qualification worker is `analysis/tests/ilvis0_timing_qualification_worker.py`;
it uses four numerical threads, one sealed test batch and a ten-minute timeout.
Completed batches cannot restart. Only complete software qualification permits
the separately frozen four-start observed comparison described in the plan.

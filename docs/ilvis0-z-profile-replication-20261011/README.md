# Z calibration on a preselected different recording

This grid checks whether calibration robustness transfers to the **earliest recording
already predeclared in the replication ledger**. Selection did not use model fits.
This is a whole-stretch calibration check, separate from the deferred training/prediction
replication experiment.

An IMU (inertial measurement unit) measures turning and acceleration. The file is
`ILVIS0_applanix_57289_610_LVIS_38614965.013`, IMU21, September 24, 2015.
The saved interval is **12:47:53–12:55:12 UTC, 439 seconds**, with median ground
speed **793.61 km/h** and minimum **788.77 km/h**. Original SHA-256:
`b1b624d9c5d736b411e6faa58b53000f1884d01563615b2681413234fcd48363`.
Reuse the complete interval and original measurements, without recalculating eligibility.

The [plan](PLAN.md) specifies the same nine Z gain/offset combinations and three
models as the [first grid](../ilvis0-z-profile-audit-20261011/README.md), with fixed-zero
upstream removal, original integration and packet-header timing. It has its own
**27-start, 5,400-sweep ceiling, no retries**. The first pass contained unfinished
globe fits; their labels remain unchanged.

The [sequential launcher](../../analysis/tests/ilvis0_z_profile_sequence.py) starts this
grid after the [processing-assumption grid](../ilvis0-z-profile-removal-20261011/README.md)
publishes, retaining both locks and using one worker/two threads. Preparation, launch
and recovery follow that guide. Completed publication only uses
`analysis/tests/ilvis0_z_profile_followup.py --study replication --package-only` with
the frozen environment.

Another date checks transfer across recorded conditions; it does not establish an
independent physical instrument or verified installation continuity. This recording
already appeared in the archive analysis, so it is development evidence, not unseen
confirmation. Group1 fused navigation supplies no inertial evidence. The second
predeclared recording and further processing cases are outside this allowance.
Statistical decisions remain abstentions; field comparisons do not establish its cause.

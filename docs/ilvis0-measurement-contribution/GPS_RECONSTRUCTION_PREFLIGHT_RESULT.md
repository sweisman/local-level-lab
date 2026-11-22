# Satellite data are available for all 21 pilot candidates

All **48,099 selected GPS position times** matched a unique satellite
measurement record from the same receiver. The recorded L1 ranges and
broadcast orbit data support a position and clock calculation at every
selected time across all 21 streams.

| GPS input check | L1 | Dual frequency |
|---|---:|---:|
| Selected epochs with at least five usable GPS ranges and full position/clock rank | 48,099/48,099 | 48,081/48,099 |
| Sources with that coverage at every selected epoch | 21/21 | 20/21 |

The check evaluated satellite geometry at the receiver's reported position.
It required the original millisecond-tagged measurements, the same
recorded orbit and range checks as the earlier receiver-only workflow,
and a five-degree elevation mask. It kept the original time bounds and
left partial receiver records outside the checked span. No position or
inertial fit ran. The geometry checks support starting a separately frozen
GPS reconstruction, with the result compared to the onboard reports.
Satellite and atmospheric errors may still be shared by both position
methods.

The [coverage ledger](raw-gps-preflight-coverage.csv) and
[verification receipt](raw-gps-preflight-receipt.json) preserve all 21
source outcomes. The [plan](GPS_RECONSTRUCTION_PREFLIGHT_PLAN.md) fixes
the epochs and allowances. The run closed all 21 tasks on two threads.
All 31 focused receiver, positioning and workflow checks passed.

The [reconstruction pilot](GPS_RECONSTRUCTION_PILOT_PLAN.md) now has
[two frozen recordings and 1,112 selected epochs](gps-reconstruction-pilot-selection.json),
with a total allowance of 2,224 position solutions across the two methods.
The position check uses the existing geodetic coordinate convention.
[The completed pilot](GPS_RECONSTRUCTION_PILOT_RESULT.md) recovered all
2,224 positions and measured their processing differences.
The recorded inertial comparison remains a separate step.

The [two-group extension](GPS_RECONSTRUCTION_EXTENSION_RESULT.md) verified
both methods at 586 IMU8 and 538 IMU21 GPS epochs from the remaining
preselected groups. All 2,248 position solves converged.

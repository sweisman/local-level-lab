# Planned ESA interval selection

The ESA recording supplies much longer observations at lower ground speeds than
the original archive cohort. Its selection policy must reflect that geometry.
The existing 53 stretches and their criteria remain unchanged.

This is a **development proposal**, not a frozen selection or a finding. It is
based on receiver trajectory, source completeness and the survey report, before
any ESA Earth-model fitting. Reported survey-line boundaries describe the survey
and do not automatically define eligible intervals.

The [confirmation reservation](../analysis-provenance/README.md) fixes recording
187 as development material and protects the other cataloged groups. This policy
may screen protected groups using receiver observations alone. It must not use
model outcomes, tune thresholds to retain a preferred result, or move a protected
group into development. Selection and confirmation identities are frozen before
protected model evaluation.

## Proposed initial cohort

| Requirement | Proposed rule | Purpose |
|---|---|---|
| Source completeness | Intact full-file hash, supported format, finite values and strictly increasing timestamps | Establish usable observations without repairing them. |
| Timing continuity | Split at IMU gaps above 1.5 nominal periods, GNSS gaps above 0.75 s, or configuration/time discontinuities | Avoid bridging unsupported observations. |
| Duration | At least **20 continuous minutes** after motion exclusions | Use the longer records to compensate for slower travel. |
| Ground speed | Every supported receiver sample at least **180 km/h** | Focus on sustained flight rather than ground operations. |
| Traveled distance | At least **60 km**, calculated from the independent receiver trajectory | Preserve substantial accumulated change of local level. |
| Low maneuvering | Ten-second trajectory windows: median absolute vertical speed at most **1 m/s**, absolute course-rate at most **0.02°/s** | Screen climbs and aircraft turns using receiver data. |
| Maneuver margin | Exclude **30 seconds** before and after failed motion windows | Avoid fitting through poorly isolated maneuver transitions. |
| Receiver quality | Finite positive position covariance diagonals; horizontal standard deviations at most **5 m**, vertical at most **10 m**, PDOP at most **4**, at least **8** reported satellites | Reject unsupported positions using recorded quality fields. |

At 180 km/h, twenty minutes covers 60 km. The distance is somewhat greater than
the minimum 46.7 km covered by the original four-minute, 700 km/h requirement.
This is a geometric design comparison, not evidence derived from the gyro.
GNSS coordinates and their geodetic construction must remain explicit in later
model comparisons.

Use complete retained stretches, with exact source hash, GPS week/time, UTC bounds,
duration, speed, distance, height and heading summaries in a durable inventory.
Preserve all rejected intervals and reasons. Do not treat subwindows of one
recording as independent flights. Do not use the gyro's agreement with a physical
model, or the supplied fused navigation answer, to choose intervals.

## Required qualification before use

Implement cheap deterministic controls for gaps, time ordering, heading wrap,
nonuniform timestamps, motion margins, quality failures and boundary inclusivity.
Compute course changes from receiver velocity with actual timestamps; do not
interpolate measurements. Define window edge coverage and behavior at zero speed
explicitly. Freeze one version of the policy and its inputs before evaluating it.
Publish its results even if no intervals qualify; changed rules require a new
inventory version rather than overwriting an unfavorable outcome.

The first selected recording has 8.49 hours of IMU observations and a GNSS-only
PPP export described by the survey report. Its longest reported line is 57.4
minutes at about 263 km/h but changes ellipsoid height by about 390 m. Whether
the motion rules retain that line or split it must be determined by the declared
trajectory calculation.

Selection alone authorizes no model-fitting campaign. The IMU logs engineering-unit
rates and accelerations in reported aircraft axes, rather than Applanix integer
increments. The observation adapter, integration clock, antenna lever arm,
processing assumptions and physical error bounds need separate qualification.
No existing decision threshold or sensor-performance assumption transfers
automatically to ESA or Wuhan recordings.

[Data-source inventory](README.md) · [Further analyses](../NEXT_STEPS.md).

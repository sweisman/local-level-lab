# Stretch analytics: measurements, geometry and numerical outcomes

Snapshot: **2026-10-13T12:36:05.226108+00:00**. All **53** preselected stretches are included, including unfinished comparisons. The summary table remains unchanged. These descriptive calculations perform **no fits or forward-model predictions**, change no selection, and do not relabel findings.

- [Comprehensive stretch CSV](stretch-analytics.csv): one row per stretch; all six latest saved primary costs and stopping outcomes.
- [Fit history CSV](fit-analytics.csv): original fits, qualified-subset fits, controls/repeats and atomically saved wider-recovery attempts, retained separately.
- [Shared-leg pair CSV](shared-leg-pairs.csv): matched-time differences for every overlapping close track, with the three priority pairs marked.

## Rates and reference frames

An inertial measurement unit (IMU) records angular increments. Raw native X/Y/Z means are sums of signed integer increments times the separately validated IMU8/IMU21 scale, divided by accumulated nominal 200 Hz time. Header-clock means and cumulative clock difference are also retained. No fitted bias, gain, Earth field or transport prediction is subtracted. Means include real aircraft motion and instrument errors. Recorded mounting-message rotations produce the aircraft-axis means; their legacy field interpretation remains inferred.

Track axes are **across-left (port), along-track (forward), down**. All rates are degrees/hour. `level_course_proxy_mean_*` assumes zero bank, pitch and crab, takes the recorded aircraft axes as aligned with ground course, and subtracts only the GPS course turn from down. It is a restricted diagnostic, not a fully motion-corrected observation.

`fused_context_corrected_mean_*` rotates the raw increment means using Group-1 roll/pitch/heading, subtracts body angular motion calculated from changes in those Euler angles, then projects into ground-track axes. **Group-1 fused gyro rates are never used.** This gives a broader motion/context diagnostic, but the attitude itself comes from fused navigation, so these fields are **not independent evidence of Earth shape or a background field**. Independently established motion-corrected rate columns remain unavailable. Corrections require at least 95% supported one-second coverage; blank fields mean unavailable, never zero. Coverage fractions are retained.

Fused heading and heading-minus-course crab are labeled context. They help expose a wrong axis assumption; they do not supply independent body attitude. Original increments are not interpolated, repaired or overwritten.

## Geometry predictions

North/east velocities come from consecutive primary-receiver coordinates, not fused INS velocities. These descriptive proxies use a stated spherical radius **6,371,000 m**; they are not raw GNSS velocity observables or the exact ellipsoidal forward-model likelihood. Latitude/longitude rates, height and ground speed are preserved alongside them.

In local north/east/down axes the sphere transport prediction is `(cos(latitude) × longitude_rate, −latitude_rate, −sin(latitude) × longitude_rate)`. In level track axes this is `(v/R, 0, −sin(latitude) × longitude_rate)`. The specified stationary disc predicts `(0, 0, −longitude_rate)`. The signs follow across-left and down-positive conventions. These are **transport-only** predictions: the background-field term is separate and is not subtracted from measured rates. A southbound leg has a horizontal sphere term even when disc yaw is near zero; an oblique leg generally has both horizontal tilt and longitude-related yaw. Course alone cannot replace these quantities.

## Stopping and shared tracks

Every model is retained under both processing cases. `cost` is the last saved residual sum of squares, including unfinished endpoints; `stop_reason` separates budget, stall, stability check, stationarity check and execution error. Original messages, stationarity and active bounds remain available. A last cost from an unfinished fit is not a model exclusion or a tie. The published disposition remains the latest **qualified whole-stretch** comparison; partial wider-recovery fits do not change it. `latest_repeat_status` and `disposition_pending_reason` distinguish unfinished primaries, failed repeats and pending sealed qualification. Passing a repeat fit alone does not establish its required cost/track agreement; that remains the worker's sealed qualification.

A shared-leg ID groups simultaneous receiver tracks with at least three identical UTC receiver epochs, maximum horizontal separation ≤1 km and height separation ≤300 m. This is a documented same-track candidate, not proof of an aircraft identity or unchanged instrument installation. Distinct instruments and originals remain separate. Pair differences use only common complete UTC-second bins inside the shared interval, with no interpolation. Each difference is **left minus right**, with both mean difference and RMS difference retained. Aircraft-axis raw differences, restricted track proxies and fused-context corrections are separate. Differences alone cannot assign the cause to hardware versus mounting, processing, timing or solver behavior.

After the current recovery finishes, overlapping legs with mismatched completion are the next numerical priority, beginning with the three marked pairs. The current worker and its frozen allowance remain unchanged.

## Column dictionary

Original inventory columns retain source hash, exact UTC bounds, configuration and disposition. `raw_dtheta_*_sum_counts` preserve the selected signed integer totals. `native_samples`, both durations and both clock means describe completeness and scaling. `shared_leg_members` lists related stretch IDs. `bias1_*__MODEL__FIELD` columns contain each saved primary endpoint; full nuisance values are in the fit-history `parameters` column. `result_origin` distinguishes original, qualified-subset and unfinished wider-run outputs. The CSV headers are the complete machine-readable field list.

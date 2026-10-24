# Planned full-motion ESA selection

Version 1 sought quiet flight and found no eligible stretches. It remains
unchanged. This separate version will select intervals for the now-tested
full-motion calculation, which reconstructs aircraft turns and climbs from the
IMU (inertial measurement unit). It will not label those intervals level or quiet.

## Rules to freeze before the new inventory

Keep the original source-integrity, timing-support and receiver-quality rules:
split at receiver gaps above 0.75 seconds, sequence gaps, unsupported IMU timing
or configuration changes. Require every retained receiver sample to have speed
at least 180 km/h, reported horizontal standard deviations at most 5 m, height
standard deviation at most 10 m, PDOP at most 4 and at least eight satellites.
Retain maximal supported runs lasting at least 20 minutes and covering at least
60 km. Do not interpolate observations or join unsupported gaps.

Add validation of the full reported north/east/up covariance, using the
[shared error policy](../ESA_ERROR_POLICY.md). Invalid matrices exclude the
affected observations; a working uncertainty floor cannot repair them.
Coordinates must support the nonpolar receiver chart used by the fitter.

Remove the quiet-motion veto and its maneuver margins in this version only.
Report recorded vertical speed, heading changes, height range and route
summaries. These describe sampled motion; they do not certify an unobserved
instantaneous-motion bound. Later numerical and physical-adequacy checks remain
mandatory. Selection guarantees neither successful fitting nor a scientific result.

## Implementation and checks

Refactor the existing `lll.airquantumgrav_selection` implementation around a
shared selection engine. Keep the public version-1 entry point and its default
output unchanged. Add an explicit full-motion entry point with its own version
and policy description; do not copy the complete selector or worker.

Test version-1 compatibility against its frozen implementation, using small
deterministic trajectories. Test version-2 turns and climbs, covariance failures,
chart support, quality boundaries, gaps, exact duration/distance boundaries and
rejection reasons. Confirm that gyro values and model outcomes are not inputs.

Only after source-bound tests pass, freeze a new finite inventory on development
recording 187. Reuse its established integrity/support evidence and preserve all
rejected runs. No model fitting or protected-outcome inspection belongs to this
inventory. The first observed pilot, its interval choice, weighting, starts,
adequacy screens, thread allocation and finite allowance need a separate freeze.

[Original version-1 policy](ESA_SELECTION_V1.md) ·
[Generated full-motion checks](../esa-training-forecast-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

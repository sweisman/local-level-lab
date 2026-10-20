# ESA receiver-only selection, version 1

This implements the existing twenty-minute, 180 km/h, 60 km proposal. It selects
development recording 187 using receiver measurements and preserved source
completeness metadata. Gyroscope values, fused attitude and model costs are not
selection inputs. The other seven flight groups remain protected.

The policy has the following explicit calculation conventions, fixed before
evaluating the receiver file:

- Use recorded north/east velocity for speed and course, and recorded upward
  velocity for climb rate. Integrate horizontal speed by the trapezoidal rule
  over actual receiver intervals for traveled distance. No model-specific Earth
  radius or gyroscope observation enters the distance calculation.
- Split at receiver gaps above 0.75 seconds or discontinuous sequence numbers.
  Reject duplicate/reversed times and unsupported week/layout changes. Require
  source timing support from the completed IMU inspection, with no reported gaps
  above 1.5 nominal periods. An incomplete integrity check is not a selection pass.
- Evaluate centered closed ten-second windows. Both edges must be bracketed
  within the same continuous receiver block. Use the median absolute upward
  speed and median absolute course rate from adjacent recorded velocities,
  divided by their actual timestamp differences. Wrap course differences to
  the signed interval from −180° to +180°. Zero speed cannot define course.
- A failed motion window excludes its entire ten-second support plus thirty
  seconds on each side. Incomplete edge windows are unsupported, not extrapolated.
  Speed and receiver-quality failures exclude their own epochs; no maneuver is
  invented from a quality failure.
- Require speed at every retained epoch to be at least 180 km/h, position
  covariance diagonals positive, north/east standard deviations each at most
  5 m, height standard deviation at most 10 m, PDOP at most 4 and a sum of at
  least eight reported constellation satellite counts. These are reported
  quality indicators, not independently calibrated covariance.
- Keep maximal contiguous runs of supported epochs. Accept a run only when its
  endpoint duration is at least 1,200 seconds and integrated distance at least
  60,000 m. Threshold equality passes. Preserve rejected runs and every excluded
  epoch with reasons. Do not combine runs across a gap or exclusion.

Publish file/hash, GPS week/time, receiver-reported UTC bounds, duration, distance,
speed, latitude, height and course summaries. Report source cadence, policy
version, rejection counts and original row indices. Reported survey-line names
remain descriptive; they neither determine nor override selection.

## Rates are not logged increments

The engineering-unit adapter preserves the reported acceleration and angular
rate. A right-endpoint rectangular integration hypothesis may multiply them by
the actual adjacent time difference to construct increments. Those are explicitly
constructed values, not newly discovered instrument increments. The first row
has no preceding support; gaps remain unsupported. This arithmetic check alone
does not resolve sampling phase, filtering, coning/sculling, mounting or latency.

The initial inventory reads at most 100,000 receiver epochs from one development
file, with a 300-second cooperative wall allowance, four numerical threads,
zero raw-IMU reads, optimizer starts or native integrations, and no retries.
Freeze source, input, policy and environment hashes before execution. Publish a
zero-eligible outcome without changing thresholds or screening protected outcomes.

[Original proposal](ELIGIBILITY_PLAN.md) · [Reservation](../analysis-provenance/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

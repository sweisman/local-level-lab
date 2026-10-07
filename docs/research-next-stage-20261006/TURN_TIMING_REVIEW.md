# What changing the IMU-turn timing achieved

Changing turn timing helps some individual model comparisons, but the tested schedules
still do not support a decision across both descriptions of wind uncertainty.

The bounded search used the 11 observed two-/three-hour windows that had passed a previous
motion, duration and heading screen. It scored eight schedules per window, 88 in total,
in 6.41 seconds. Earlier passing schedules were included, followed by reproducible samples
from a safe five-minute grid. New samples had three to six turns, at least ten minutes apart.
Aircraft-maneuver buffers and the existing heading and duration requirements were preserved.
Rejected schedules and their reasons were saved alongside all evaluated schedules.

The diagnostic ranks schedules by whether both globe/disc comparisons pass at the nominal
states under both wind candidates, then by the weakest margin above the retention threshold,
then by the weakest model-contrast information. It uses the shared contrast criterion.
This is a nominal-state diagnostic, not the full-envelope optimizer or candidate acceptance.

None of the 88 schedules passed both globe/disc comparisons across the two wind candidates.
No individual pair passed across both candidates either. Under the more restrictive physical
wind/airspeed candidate alone, ten schedules passed one or two individual comparisons at
nominal settings: nine on Chicago–Los Angeles and one on Abu Dhabi–Chicago. These yielded
16 nominally passing schedule/pair combinations. The broader wind candidate failed every pair.
Selecting the restrictive candidate because it passes would not justify its assumptions.

Small follow-up checks used exact states from the registered physical-wind envelope:
reference airspeed, zero wind and some wind drifts, forward-angle offsets of 0° and ±15°,
three model anchors and nominal mount epochs. At most 30 states were checked per schedule,
248 in total, taking 0.86 seconds. Five of the 16 nominal schedule/pair passes failed in
this subset. Eleven found no failure before the cap; those results remain inconclusive.
The windows overlap and were chosen after development screening, so none is independent
validation evidence.

| Comparison under physical wind only | Nominal schedule/pair passes | Disproved in the small check | Still unresolved |
|---|---:|---:|---:|
| Rotating versus stationary globe | 7 | 3 | 4 |
| Stationary globe versus disc | 9 | 2 | 7 |
| Rotating globe versus disc | 0 | 0 | 0 |

The strongest surviving stationary-globe-versus-disc comparison in this subset uses the
Chicago–Los Angeles window starting 60 minutes after the first recorded position and lasting
two hours, with IMU turns at minutes 5, 15, 30, 40 and 90 within the window. Its worst checked
retained fraction is 0.404683 against a threshold of 0.312250. Its rotating-globe-versus-disc
comparison still fails nominally, and the broader wind candidate still fails. This schedule
is a development control, not a recommended collection protocol.

The complete registered physical-wind envelope check for that one partial comparison was
authorized and completed on 2026-10-07: all 15,210 SVD states, in 29.70 seconds using one
numerical thread, within the two-minute cap. It includes the registered airspeed levels/drifts,
wind states, both noise levels, forward-angle offsets and individual mount-epoch variations.
The stationary-globe/disc comparison passes this finite grid. Its worst direct-pair retention
is 0.365100 against the 0.312250 threshold, a margin of 0.052850. Worst contrast information
is 20.4842. The worst retention was independently reproduced using a separate rotation
implementation for the limiting mount perturbation; all source/input/environment hashes match.

| Comparison | Worst direct-pair retention | Direct-pair design criterion | Worst retention after global rank cutoff |
|---|---:|---|---:|
| Rotating versus stationary globe | 0.314615 | Pass, narrowly | 0.312069, fails |
| Stationary globe versus disc | 0.365100 | Pass | 0.362165, passes |
| Rotating globe versus disc | 0.144197 | Fails | 0.128649, fails |

The global model-test rank is one in every state. The rotation comparison's slight pass
applies to the direct pair-specific calculation; it fails after the global rank cutoff.
This illustrates why partial comparisons and global three-model eligibility are distinct.
The targeted stationary-globe/disc comparison passes under both calculations. The rotating-
globe/disc comparison still fails, and the broader wind candidate already fails nominally.

This is useful separation in assumed geometry on an actual recorded route, conditional on
the physical wind/airspeed model. It is not an IMU measurement, a full-pipeline acceptance,
a validated decision or a guarantee beyond the finite grid. The restrictive wind assumptions
still need justification. The next step is a separately budgeted matched simulated-IMU replay
of this frozen route/window/schedule under the three truths and combined wind plus sensor drift,
including recovered axes and both wind candidates. Calibration follows only if that evidence
supports a useful declared domain.

No flights were simulated and no gyro data were fitted. The scientific implementation and
acceptance thresholds are unchanged. Fifty-two existing motion, direction and eligibility
checks passed in 1.43 seconds; three new freeze/deadline guards passed in 0.38 seconds.

Reproducible helpers are `analysis/tests/screen_safe_turn_timings.py`,
`check_partial_timing_counterexamples.py` and `check_observed_pair_envelope.py` in that
directory. Their results, rejected timings, source hashes and frozen execution plan are
`safe-turn-timing-screen.json`, `partial-timing-counterexamples.json` and
`observed-pair-envelope-plan.json` here; the completed check is
`observed-pair-envelope-result.json`. Full-envelope execution requires an explicit `--run`;
it refuses changed science, inputs, helper or numerical environment and writes no pass if
the time limit expires.

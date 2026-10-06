# Route direction and partial shape evidence

The latest cheap screen compares five previously prepared 75-minute airline paths, the
120-minute Abu Dhabi–Chicago pilot path, and a counterfactual traversal of that longer path
in the opposite direction. It tests three fixed IMU-turn patterns on each path. This is
21 controls, not a search over all routes or turn schedules, and the reversed path is not
an observed return flight.

Twelve patterns passed the buffered aircraft-motion check. Their two wind descriptions gave
24 candidate evaluations, including two preserved failures with no qualifying bins. The
remaining candidates each used three physical-model anchors, zero nuisance offsets and
assumed noise. The screen took 0.54 seconds and generated no flight or noisy IMU recording.

The useful clue is that **direction can improve shape separation without resolving rotation**.
With six turns at minutes 10/30/50/70/90/110, the reversed longer path keeps 85 analytic cruise
minutes and adequate heading diversity. Under the physical wind/airspeed correction, its two
globe/disc contrast retentions are 0.415 and 0.436, above the required 0.31225. Its globe-rotation
contrast remains below the criterion at 0.298. The same turn pattern on the actual westbound
path gives globe/disc retentions 0.125 and 0.305. Both still fail.

The reversed path fails under the broader wind-coefficient correction: its globe/disc
retentions are 0.254 and 0.294. Consequently **no tested pattern passes both shape contrasts
under both wind descriptions**, even at nominal conditions. This does not justify choosing
the physical wind model solely because it gives a preferred result. Its assumptions must
be supported independently and tested across the nuisance envelope and complete pipeline.

The prepared Seattle–Keflavik path has another nominal shape-only pass under physical wind,
with retentions 0.333 and 0.416 using turns at 20/40/60 minutes. It retains only 55 analytic
minutes and insufficient heading diversity, so it fails the unchanged observable requirements.
A favorable contrast calculation cannot override those exclusions.

`analysis/tests/screen_route_directions.py` preserves all patterns, motion checks, failures,
individual anchors and input/source hashes in `route-direction-screen.json`. It uses the same
dynamic bias, wind, airspeed and forward-angle nuisance families; none was removed to force
separation. Two software controls check that reversing a path preserves positions, support
and speed while reversing velocity, climb rate and course rate, and that irregular sampling
is refused. These passed in 0.39 seconds.

These are local tangent controls with assumed C2 motion and known IMU axes. They do not check
the full nuisance envelope, recovered orientation, actual drift amplitudes, bootstrap,
empirical power or error rates. A nominal pass is not scientific acceptance. The completed
airline pilots and their abstentions remain unchanged.

Next compare additional observed eastbound or suitably turning windows under the explicit
shape objective, keeping the nuisance space and motion guards. Bench measurements may later
support more precise drift assumptions. A complete-envelope or simulated-flight follow-up
needs a bounded plan and compute budget; no further flight attempts are authorized.

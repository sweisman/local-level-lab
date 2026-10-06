# Smoother-route and matched-reference pilot

An **IMU (inertial measurement unit)** measures acceleration and turning. This pilot
compares wind corrections on simulated IMU readings along an archived Frankfurt–Johannesburg
route. It uses an explicitly smoother assumed path and compares GPS-derived bank change
with IMU roll after applying the same smoothing.

**Initial three evaluations complete.** All fits converged without analysis failures, but
none passed the scientific gate or supported a pairwise decision. The three-case authorization
is exhausted; the remaining 15 proposed evaluations are unrun and unapproved. Previous failures
remain preserved. This pilot uses fresh seed 600901 and no bootstrap or empirical thresholds.
The completed cases share one generating condition under three corrections. The complete
18-case proposal shares six generating conditions; it is not 18 independent null flights.

The candidates are the existing wind correction, physical wind/airspeed correction, and
physical correction with optional mount-ambiguity comparison. Each uses the new measured
angle uncertainty. Three model truths and two scenarios cover wind with mixed IMU bias and
wind with bias, correlated noise and temperature effects. IMU turns at minutes 20, 40 and 60
pass the declared buffered motion check on the assumed smoother path.

The matched method applies a common 30-second filter and estimates angle uncertainty from
the joint GPS/IMU relationship with a 60-second covariance window. It separates missing-data
intervals and requires enough supported duration and frequent GPS. Existing correlation and
signal-strength limits remain in place. Earlier saved sessions gave a provisional standard
deviation of about 0.58°; the fresh pilot gives about 0.69°. Independent-error assumptions do not
cover systematic alignment error, correlated measurement errors or unmodeled motion.

Controlled tests include continuous sub-degree bank corrections, additional body yaw and an
occasional larger transient. Small aircraft corrections are physical motion, rather than
automatically GPS error. Qualitative infrared footage from a right passenger window used a
135 mm lens and QHY585 mono camera, showing frequent small view changes and occasional larger
ones. No footage has been ingested or converted into calibrated attitude or timing measurements.
The small fixed noise panel is a software check, not a coverage experiment.

Reference footage supplied after the pilot: [infrared flight video](https://www.youtube.com/watch?v=Yw-oXwjoJ3A),
reported at roughly 4 fps with a horizontal field of view about 4.75°. A horizontal displacement
of 1% of the full, uncropped image width therefore corresponds to approximately 0.0475° of
scene angle. The camera was on a tripod resting on the tray, reported as stable as practical.
The footage was not fetched or measured here. Tray/tripod rigidity, cropping, capture
versus playback timing and scene distance must be established before interpreting image motion
as aircraft attitude or deriving angular rates. This information does not change simulation
parameters or acceptance gates.

The new path preserves supplied coordinates, heights and gaps with continuous acceleration
inside supported blocks. Natural endpoint curvature, possible overshoot and motion between
sparse observations remain assumptions. Real-device checks, full-pipeline identifiability,
fresh calibration and independent validation remain necessary.

## Completed results

The forward reference passed, with gain 0.785, explained variation 0.750 and estimated angle
uncertainty 0.69°. Only 57 minutes of cruise survived preprocessing, below the required 60.
Retained heading span was 15.5°, and the shared heading-diversity requirement also failed.
Every intended model contrast failed the conservative nuisance-envelope design gate.

The fitted model-test ranks were 0 for the original wind correction and 1 for both physical
wind candidates; the worst design rank was 0 for all three. These are different quantities.
Even before truncating singular directions, worst contrast retention was below the declared
0.31225 threshold. The physical candidate retained more information, but still insufficient
separation. No acceptance threshold was relaxed.

No magnetic movement boundaries were flagged. Retained and excluded paths gave identical
coefficients, but their comparison could not establish agreement because neither path had
identifiable contrasts. This was an unavailable scientific comparison, not evidence of mount
movement or different numerical answers.

The evaluations took 6.26, 72.62 and 123.96 seconds: 202.84 seconds in total, about 131 seconds
of observed wall time with two workers. The saved run occupied 39,234,307 bytes at review.
These timings cover one condition with no bootstrap; they do not predict calibration cost.
`results-review.json` records the results and timing basis. Helper:
`analysis/tests/review_matched_pilot.py`. The append-only execution records remain in `run/`.

## Next route check

A cheap screen of five archived 75-minute windows applies the existing heading-duration rule
to the assumed smoother paths before any IMU exclusions. Only AUH–ORD passes this optimistic
screen. ORD–LAX, SEA–KEF and FRA–JNB lack enough heading separation. ORD–AUH has a wide overall
span, but its distant directions are too brief to pass the duration requirement.
`route-screening.json` records this screen; helper: `analysis/tests/review_route_geometry.py`.
It runs no flight simulation, science fit or identifiability calculation. Passing this screen
does not establish that preprocessing will retain enough cruise or useful model information.

Next, review route windows and IMU-turn timing against the shared observable gates before
another expensive fit. Do not spend the remaining cases on the current window or proceed
to calibration. Additional flight evaluations require a new explicit budget.

### Motion and wider-window preflight

The stricter analytic motion screen rejects all five initially prepared windows. Abu Dhabi–
Chicago has no continuous ten-minute interval under the joint motion mask; without the
bank-rate condition, only one interval qualifies. Course and reported-height changes also
break support. This is assumed motion derived from sparse public positions, not a measurement
of actual aircraft attitude. The analytic screen differs from complete cruise preprocessing.

Across all seven saved tracks, 192 overlapping 75-minute windows have sufficient observed
position coverage. One cannot be evaluated because reported height is missing. None passes
with a safe three-turn schedule on the five-minute grid; 9,640 schedules were screened.
Only one window has both heading diversity and 60 screened cruise minutes before turns,
leaving no margin for the turn exclusions.

Twenty-one 90-, 105- and 120-minute extensions around that window were then checked;
19 pass the observable screen. The best 120-minute Abu Dhabi–Chicago candidate retains
91 screened minutes with turns at 25/50/85 minutes, and seven minutes of heading-duration
margin. This is a new exploratory candidate, not an adopted protocol or an identifiability
result. The [extended pilot proposal](../extended-airline-pilot-20261006/README.md) freezes
a fresh comparison. Its subsequently authorized three-case prefix is now complete: 97 cruise
minutes and adequate heading diversity survived, but every intended design contrast failed.
All fits converged without analysis failures; the full results and exhausted allowance are
recorded in that pilot's README. No additional evaluations are authorized.

Reports: `turn-preflight.json`, `turn-motion-review.json`, `window-preflight.json` and
`extended-window-preflight.json`. Helpers: `analysis/tests/preflight_route_turns.py`,
`preflight_route_windows.py`, `preflight_extended_window.py`. Four focused controls pass,
including missing coverage, unsafe turns, heading sufficiency and rotated reference directions.
No flight, fit or SVD was run during these screens; original records and gates are unchanged.

## Technical freeze

`matched-forward-1` in `analysis/lll/forward_reference.py` requires explicit
`forward_reference='matched'`, `research_candidate=True` and `forward_uncertainty=True`.
Default analysis remains legacy. The method/policy enter inference provenance; the source
manifest hashes the new module. Research CLI accepts
`--forward-reference matched --forward-uncertainty --research-candidate`.

`plan.json` freezes source, one-thread environment, candidate jobs and configuration.
`preparation-review.json` records tasks, turn checks and limitations. Helper:
`analysis/tests/prepare_matched_pilot.py`. Source hash:
`82c882d2abf351cb0feb0e8efa237702d1deeccd475d682960419677bf479412`.
Worker environment: `20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`.
Plan: `e3064a50835a631d6968b11757d8451cff1e87c20e9ae74bf02580f2fa06bf78`.
Route: `5e69715fb544fd45612318a48f15136f7df97354289ecfdbc939e7dc16229d83`.

The completed authorized prefix used two single-thread workers with this command, recorded
here for provenance, not as permission to launch or extend the campaign:

```sh
/home/sweisman/venv/bin/python analysis/tests/sharded_campaign.py run docs/matched-airline-pilot-20261006/plan.json --output docs/matched-airline-pilot-20261006/run --workers 2 --attempt-limit 3 --detach
```

`run/status.json` is `budget_complete`, with three completed and 15 missing evaluations;
both shards are complete. No worker is active. Detached execution follows the
[runner instructions](../sharded-campaigns-20261006/README.md). No wall-time ceiling was
encoded. Further evaluations need another budget.
Do not retry exhausted original tasks or substitute the simulator's known axis into inference.

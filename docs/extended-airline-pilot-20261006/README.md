# Extended Abu Dhabi–Chicago development pilot

An **IMU (inertial measurement unit)** measures acceleration and turning. This proposal uses
simulated IMU readings along a longer part of an actual airline position track. It asks
whether a route that passes preliminary motion and heading checks also preserves enough
information to distinguish the physical models once wind and sensor uncertainties are fitted.

**Initial three evaluations complete.** All fits converged with no analysis failures, but
none passed the model-separation gate. This pilot's three-attempt allowance is exhausted;
the remaining 15 cases are unrun and unapproved. Earlier pilots also remain complete and spent.

The candidate is a 120-minute window of the 2025-08-19 Etihad 9 Abu Dhabi–Chicago track,
from elapsed track seconds 40,200 to 47,400. On the explicitly assumed smoother path, IMU
turns at minutes **25, 50 and 85** avoid the buffered aircraft-motion intervals. The screen
retains **91 minutes** of cruise and passes the shared heading-duration rule with a
**seven-minute margin**. Screened minutes per mounting epoch are 23, 20, 23 and 25.

The recorded positions cover about 99.58% of the window. Motion between fixes, the reported
height reference and the quality of hypothetical frequent GPS remain assumptions. This
route now passes the forward-reference check but fails the nuisance-envelope identifiability gate.
The turn schedule was ranked by screened geometry, not by the scientific optimizer.

The proposal compares the existing wind correction, the physical wind/airspeed correction,
and the physical correction with mount-ambiguity agreement. All use the matched measured
forward reference, dynamic sensor bias and direct pairwise profiles. The initial three cases
share rotating-globe truth with wind plus mixed bias; the full 18-case grid contains three
truths and two composite nuisance scenarios. These matched cases are not independent null
draws. Bootstrap is zero and no calibrated decisions or false-rejection bounds can result.

## Completed result

The complete preprocessing retained **97 cruise minutes**, with a **51.1° heading span** and
sufficient time in distinct directions. These differ from the preliminary screen's 91 minutes:
the screen and complete preprocessing use different bin and motion selection. The previous
duration/heading exclusions are gone. The matched forward reference passed with gain 0.979,
explained variation 0.925 and estimated angular uncertainty **2.19°**. Its uncertainty coverage
remains unvalidated.

All three fitted model-test ranks and worst design ranks were zero. Every primary and pairwise
decision abstained. Even before the singular-value cutoff, the physical wind candidate's worst
retained fractions were about 0.175, 0.077 and 0.197 for rotating-vs-still, rotating-vs-disc and
still-vs-disc, all below the unchanged 0.31225 requirement. It preserved more information than
the existing wind correction, but still too little for acceptance. Changing the rank cutoff
alone would not resolve these retention failures.

No magnetic movement boundaries were flagged. Retained/excluded fits and pair shifts were
identical, but agreement was unavailable because both paths lacked identifiable model contrasts.
This is not evidence of mount movement or numerical disagreement.

The three evaluations took 24.29, 147.29 and 256.64 seconds: 428.21 attempt-seconds and about
**4 minutes 42 seconds wall time** with two workers. Saved execution storage was 49,961,789
bytes at review. This is one generating condition, without bootstrap; timings do not establish
calibration cost. The earlier 75-minute pilot used a different seed and route, so it is not a
controlled comparison of duration alone. `results-review.json` preserves these findings and
their timing basis; `analysis/tests/review_matched_pilot.py` reads existing results without fits.

The [saved-data diagnosis](DIAGNOSTIC_REVIEW.md) now finds smooth bias drift is the main loss
in most checked states; this westbound route also partly cancels the rotating globe's horizontal
signal. A safe six-turn pattern improves nominal separation but still fails the gate.
An analytic course-gap bug was repaired; it does not change the completed pilot.
Next compare different route directions and feasible turns while retaining the nuisance model.
Do not spend the remaining cases or begin calibration on this failed condition.

## Freeze and execution boundary

`plan.json` and `preparation-review.json` preserve the proposal. Helper:
`analysis/tests/prepare_extended_airline_pilot.py`. Fresh seed: **600902**.
Source: `82c882d2abf351cb0feb0e8efa237702d1deeccd475d682960419677bf479412`.
One-thread worker environment:
`20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`.
Plan: `d2337e3a4bbe4da89f9b446d9b49c7ca0f19f13d94172a0bb81861696549eae0`.
Route: `0dcd534e05f0621361898f0c1f6a98663aaa76635d07f9059dcb4e5719e7bf16`.

The completed prefix used two single-thread workers and the durable
[campaign runner](../sharded-campaigns-20261006/README.md). No time ceiling was encoded.
Keep completed failures, do not repeat attempts, and review preprocessing, forward reference,
design contrast retention and pairwise abstention before proposing additional spending.
`run/status.json` is `budget_complete`, with three completed and 15 missing evaluations;
both shards are complete. No worker is active and no additional attempt is authorized.
The bound plan, launch/status, journals, diagnostics and partial campaign export remain in
`run/`. Calibration, independent validation, production promotion and git operations remain separate.

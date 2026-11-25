# Adversarial review of the airborne comparison

**Date:** 25 November 2026. **Scope:** the 53-stretch NASA comparison, the code that produced it, the public wording, and what can be done next without new outside data.

This review set out to break the project's main result. It read the saved results and the code. It ran no new model fits and opened none of the reserved ESA recordings. An **IMU (inertial measurement unit)** is the aircraft instrument whose gyroscopes and accelerometers supply the measurements.

Three independent reviewers each read one part of the code without being told what the others or the saved results suggested. Every finding below was then checked against the code or the published tables. The scripts in this folder regenerate each number from the published files.

## Verdict

**The main result holds.** On all 53 stretches the measurements fit a globe far better than the tested flat disc. The review found no error in the equations or the file decoding that would change that.

Three weaknesses deserve work before the result is called confirmed:

1. Only one gyro-offset allowance was ever fitted. On a single straight leg, a disc plus a large enough gyro offset would look like a globe. The saved fits answer this across legs, but no fit has tested it directly. ([S1](#s1-only-one-gyro-offset-allowance-was-fitted))
2. Every selected stretch comes from a file where the instrument's own navigation computer reported full alignment. That computer uses globe equations. ([S2](#s2-selection-depends-on-the-instruments-own-navigation-status))
3. The disc was fitted with the background field on only 4 of 27 recording groups. ([S3](#s3-the-disc-was-rarely-given-the-background-field))

All three can be addressed with data already in the archive. [What can be done now](#what-can-be-done-without-new-outside-data)

## What held up

- **The margin is large and does not depend on solver history.** The disc's cost is at least 293 times the best globe cost on every stretch (71 times when an extra processing freedom is allowed), and about 9,000 times at the median. Across all 789 saved fit attempts, including those that stopped early, the disc's lowest cost never comes within 70 times the globe's highest. Choosing a different saved attempt for any stretch could not change the preference. `audit_attempts.py`
- **The equations are right.** An independent derivation of the motion equations for a globe and for a pole-centred disc matched the code in signs, frames, units and rotation order. The Python, C and C++ versions implement the same model.
- **The disc gets a fair start.** Each candidate begins from a velocity and heading computed with its own geometry. The measurement weights are built once and shared by every candidate. Bounds, starting point and evaluation budget were identical per candidate in the first pass.
- **The decoder is strict.** Framing, checksums, truncation, duplicate epochs, time reversals and leap-second transitions are rejected and never repaired. The navigation computer's fused solution never enters the fitted observations.
- **The published checks pass.** Five check-only verifiers and 70 focused tests passed on this checkout. [Commands](#reproducing-this-review)

## Findings on the science

Ranked by how much they matter to the main result.

### S1. Only one gyro-offset allowance was fitted

**Severity: high. Threat: the strongest objection a specialist would raise.**

Every fit allowed each gyro a constant offset of up to 1°/hour (`analysis/tests/ilvis0_segment_worker.py:31`). A tighter 0.1°/hour case was planned and deferred. No looser case was run.

Why it matters: every selected stretch is a straight, level leg. On one such leg, the turning a globe predicts (about 7.5°/hour of nose-down pitch at these speeds) is the same shape of signal as a constant pitch-gyro offset of that size. With the allowance at 1°/hour the disc cannot absorb it and loses badly. With an allowance of 8°/hour or more, the disc could probably match the globe on that one leg.

What the saved fits already show:

| Quantity, fitted under the globe with the field | Result across 53 stretches |
| --- | --- |
| Offset asked for on the roll axis | mean 0.03°/hour, spread 0.08 |
| Offset asked for on the pitch axis | mean 0.02°/hour, spread 0.10 |
| Largest combined level-axis offset | 0.38°/hour |
| Change in pitch offset as speed changes | slope −0.008 ± 0.034 |

The last row is the useful one. The stretches span ground speeds of 727 to 916 km/hour, so the globe's predicted pitch rate spans 6.5 to 8.2°/hour. If a constant gyro offset were standing in for curvature, the globe fits would need an offset that changes one-for-one with that rate. The fitted offsets do not change with speed. They are also near zero on north, east and south headings, at 42°N, 72 to 75°N and 57 to 64°S, on two IMU types, in four campaign years. `audit_offsets.py`

What is missing: this is a reading of fits that were already done, on stretches that were used for development. It is not a test that was set up in advance. A direct check would refit with wider allowances and show the size and pattern of the offset the disc then needs.

### S2. Selection depends on the instrument's own navigation status

**Severity: high. Threat: "you only kept flights where a globe-based computer was already happy."**

A stretch qualifies only if the instrument's fused navigation solution reports full alignment at every sample (`analysis/lll/ilvis0_segments.py:85`). All 53 selected stretches come from files with no unaligned samples at all. 153 of the 179 other files contain unaligned samples. Roll, climb and turn-rate limits come from the same fused solution.

That status flag is believed to reflect the computer's own uncertainty estimate, not a comparison with any Earth model, so this probably did not shape the outcome. It has not been shown.

An earlier study already removed the alignment requirement and kept every other rule. It found **five more stretches, 55.0 minutes, on four dates**, and fitted none of them. [Alignment ablation](../ilvis0-alignment-ablation/RESULT.md) A receiver-only screen also found possible stretches in 84 of the blocked files. [Archive guide](../ILVIS0.md)

### S3. The disc was rarely given the background field

**Severity: medium to high. Threat: "the globe got two tries and the disc got one."**

The globe is fitted with and without the background rotation field, and the better one is compared with the disc. The disc is fitted without the field only (`analysis/lll/ilvis0_exploratory.py:19`). The code for a disc with the field exists (`analysis/lll/ilvis0_native.c:40`), and it was used in the matched forecasts on 4 of 27 groups.

The public headline compares globe with flat, and that framing is sound. A reader can still ask whether the disc loses because of its shape or because it was denied the field. Running the disc with the field on all 53 stretches would answer that.

### S4. The losing fits are not meaningful numbers

**Severity: medium. Threat: to any sentence that ranks the two losing candidates.**

The zero-field globe and the disc do not fit. Their best attempts typically rest against 15 or 16 of the 26 permitted limits, and as many as 18 (the winning globe typically rests against 3). In 33 of 53 stretches the disc's best fit points the aircraft's nose more than 20° further from its direction of travel than the globe fit does, often by 60° to 120°. A real aircraft does not fly sideways. `audit_costs.py`, `audit_offsets.py`

So the statement "comparing just the two zero-field fits, the disc had lower cost on 18 stretches" compares two failed fits. Which one fails less depends on the size of the permitted limits and on flight direction. It says nothing about shape.

### S5. The second "processing assumption" is not neutral

**Severity: medium.**

The second processing case lets a fraction of the standard Earth rate be treated as already removed by the instrument. For the globe with the field this is a reasonable hypothesis: the fits used a fraction of 0 on 30 stretches and between 0.01 and 0.17 on the other 23, never more.

For candidates with no field, the same setting adds a rotation of the *opposite* sign (`analysis/lll/ilvis0_tangent.cpp:73`). The disc uses it: a fraction of 0.6 or more on 24 stretches, lowering its cost by up to 12.6 times. It does this by combining the extra rotation with an impossible heading. The disc still loses every stretch. `audit_parameters.py`

This error favours the disc, so it does not weaken the main result. It does mean "under both processing assumptions" should not be described as the same physics under two instrument settings.

### S6. Coverage is narrower than the counts suggest

**Severity: medium.**

The 27 recording groups are 27 flight dates. `audit_costs.py`

| Property | Count of 53 stretches |
| --- | ---: |
| From September and October 2015 | 38 |
| From 2009, 2010, 2011 | 8, 4, 3 |
| Southern Hemisphere, 56°S to 64°S | 49 |
| Northern Hemisphere, 42°N to 75°N | 4 |
| Southern stretches on courses from 106° to 213° | 49 |
| IMU type 21 | 51 |

In 2015 three recorders flew on the same aircraft, and ten pairs of selected stretches overlap in time. In practice the evidence is one flight geometry, southbound legs over the Southern Ocean, repeated on many days, plus four Arctic legs that carry most of the variety in heading and latitude.

### S7. The winning fit also presses on three limits

**Severity: medium to low.**

Under the globe with the field, the vertical gyro offset sits on its limit in 42 stretches, the vertical gyro scale in 48 and the gravity adjustment in 42. The signs are mixed, even between consecutive legs on one flight, so this is not a steady instrument error. Something in the heading and vertical channels is not modelled.

One candidate: gravity is a single constant, 9.81 m/s², for every candidate (`analysis/tests/ilvis0_segment_worker.py:341`). It does not change with latitude or height along the leg, and local gravity variations are ignored. This affects every candidate equally.

### S8. The unit conversion for the main IMU type is weakly supported

**Severity: medium to low. Unsupported, not shown to be biased.**

The factors that turn raw counts into angles and velocities were found by matching the instrument's own fused solution. No manufacturer table was located. Of the 51 stretches on IMU type 21, 20 pass both decoder checks; 14 fail the per-file check, each on the accelerometer side. [Archive guide](../ILVIS0.md)

The fit lets accelerometer scale vary by 15% and gyro scale by 2%, so errors of that size are absorbed. A gyro scale error large enough to matter would hurt the globe fits, which are the ones that work.

### S9 to S12. Smaller points

- **S9. The decision rule has no margin.** Any lower cost counts as a preference, and a fit resting on its limits counts the same as one that is not (`analysis/lll/ilvis0_shape.py:198`). In practice the smallest margin is 71 times, so no result turns on this.
- **S10. The thresholds were set after earlier trial fits.** Four minutes and 700 km/hour were chosen after exploratory fits on other files. The methodology page already says so. The selection code reads no fit output.
- **S11. Timing.** The time-base check tolerates 2 seconds, and only 12 of 53 stretches carry the tighter 1-millisecond cross-check. Fits use a fixed 5 ms per sample. A whole-second error would show as a large misfit in every candidate.
- **S12. Costs are not calibrated.** The weights assume about 1 m horizontal and 3 m vertical GPS error with 60-second correlation, and were never refitted under the looser alternative. The costs rank candidates. They are not probabilities, and fit quality should also be stated in metres.

### Not established

- Whether a known-answer test exists in which the fitter is given measurements generated on a disc and correctly prefers the disc. A limited search found none.
- Whether the retained files hold stationary minutes on the ground before take-off. Those would allow a direct check of the rotation rate at different latitudes.
- Whether raw increments were corrected inside the instrument before logging. Any removal of Earth rate would count against the reported result.

## Findings on the public wording

- **Headline.** Changed to state the shape comparison directly: 53 of 53 stretches favored a globe over the tested flat disc.
- **The "18 stretches" sentence.** Removed from the homepage and qualified on the status page, for the reason in S4.
- **Coverage.** One sentence added to the homepage describing where and when the stretches were flown (S6).
- **Gyro offsets.** The fitted offsets and their independence from speed are now stated, since they answer the most natural objection (S1).
- **Accurate as written:** the eight degrees per hour figure, the three gyro plots and their captions, the statement that the 53 stretches are not independent flights, and the limits on what seven ESA groups can establish.

## Work this review did not do

- It ran no new fits, so S1, S3 and S7 are diagnosed, not resolved.
- It did not run the full test suite or the verifiers that read the reserved ESA recordings.
- The security review of the participant server and app is in a separate note, held back from publication until its findings are fixed.

## What can be done without new outside data

The earlier plan waited on documents from other groups to bound aircraft errors at the millimetre level. That requirement comes from a fine satellite-range score on one two-minute ESA development comparison, where aircraft range error would need to stay near 2 mm. The position comparison between the three candidates is far coarser. In the two complete settings on the ESA development flight, the withheld horizontal errors were 5.18 m for the globe with the field, 2,590 m for the zero-field globe and 3,997 m for the disc. In the other two settings the disc fits did not converge. [ESA matched forecasts](../prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)

Proposed checks, in order. None has been approved or started.

| Check | What it settles | Needs |
| --- | --- | --- |
| **1. Fit the five never-fitted stretches** from the alignment ablation, under the existing method with nothing changed. | S2, and it is the first test on stretches that played no part in development. | About 30 fits. |
| **2. Wider gyro-offset allowances** (3, 10 and 30°/hour) on one stretch per flight date, for the globe and the disc. | S1. Shows the offset a disc needs and whether it follows speed and heading as a globe predicts. | About 160 fits. |
| **3. Disc with the field on all 53 stretches.** | S3. | About 106 fits. |
| **4. Aircraft records for the other 2011 and 2015 flights.** The separate one-second attitude record used for one stretch (flight RF04) is published for every flight in both campaigns. | Extends the independent motion check from 1 stretch to as many as 41. | A data order from NCAR; no fits. |
| **5. Measure instead of compare.** Fit the rotation rate and the curvature freely and report an Earth radius and a rotation rate with their spread across flight dates. | Turns a tally into a measurement. Brings forward roadmap item R01. | New fitting code; larger. |
| **6. ESA confirmation on position error.** Freeze a rule based on withheld-position error for the three candidates, with a coarse stated GPS allowance and a stated treatment of disc fits that do not converge. | Independent aircraft and instrument. | A decision to use the seven reserved groups, which can be spent once. Best left until checks 1 to 3 are done. |
| **7. A wider NASA selection** using receiver data only, from the 84 blocked files with possible stretches. | A larger set of never-fitted stretches. | A new frozen selection policy. |

Fit times were not measured in this review. Timing one fit first would turn the counts above into hours.

## Reproducing this review

From the repository root. Each script reads published tables only.

```sh
~/venv/bin/python docs/red-team-20261125/audit_costs.py docs/ilvis0-current-findings-20261015/stretch-analytics.csv
~/venv/bin/python docs/red-team-20261125/audit_parameters.py docs/ilvis0-current-findings-20261015/stretch-analytics.csv docs/ilvis0-current-findings-20261015/fit-analytics.csv
~/venv/bin/python docs/red-team-20261125/audit_offsets.py docs/ilvis0-current-findings-20261015/stretch-analytics.csv docs/ilvis0-current-findings-20261015/fit-analytics.csv
~/venv/bin/python docs/red-team-20261125/audit_attempts.py docs/ilvis0-current-findings-20261015/fit-analytics.csv
~/venv/bin/python docs/red-team-20261125/audit_selection.py docs/ilvis0-highspeed-segments-20261008/files.csv
```

Checks that passed:

```sh
~/venv/bin/python docs/build_current_status.py --check
~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check-public
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_group_zero_field check
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.ilvis0_group_evidence_current check
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_group_evidence check
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m pytest -q analysis/tests/test_applanix.py analysis/tests/test_ilvis0_forward.py analysis/tests/test_ilvis0_exploratory.py analysis/tests/test_ilvis0_shape.py analysis/tests/test_ilvis0_segments.py analysis/tests/test_ilvis0_segment_worker.py
```

[Current findings](../CURRENT_STATUS.md) · [Method](../METHODOLOGY.md) · [Next steps](../NEXT_STEPS.md) · [Study index](../STUDIES.md)

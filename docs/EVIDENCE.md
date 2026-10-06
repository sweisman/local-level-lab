# Evidence so far

An **IMU (inertial measurement unit)** measures turning and acceleration. The experiment seeks
a small, model-dependent turning signal during level flight. These results describe progress
in testing the software and experimental design. They are not measurements proving that a
real consumer-grade IMU already distinguishes the three Earth models reliably.

## Software checks

The model calculations are checked against an independent geometric calculation. This helps
catch errors that would go unnoticed if the same formulas generated and analyzed the test data.
Other automated checks cover decoding, timing, calibration, changing IMU errors, model
comparisons and data loss. They establish specific software behavior, not hardware performance.

## The two large development pilots

Two campaigns of 1,000 simulated flight attempts each exercised the analysis with wind and
changing IMU errors. Most cases passed the software acceptance checks, and all returned fits.
The first campaign contained one accepted case that wrongly rejected the model used to generate
it under the provisional decision rule. The second contained none among accepted cases.

Those campaigns used different settings and shared simulation inputs within comparisons.
They are development evidence, not thousands of interchangeable independent tests of one final
rule. Their main value was finding failure modes and showing which checks need further work.

## The geometry study

A later study completed 300 analyses over 24 selected route patterns and the existing reference
procedure. It varied latitude, heading patterns, duration, speed and IMU turns, and allowed for
wind in two different ways. Six analyses had no usable fit after protective data exclusions.
None of the 25 geometries passed every required comparison across both wind descriptions.

The audit explained several separate problems. Some ten-minute legs were too close to the
minimum steady-cruise requirement. Long legs allowed changing IMU error to imitate slow signals.
Wind could resemble mount movement in the magnetic checks. A numerical defect also made the
information calculation depend on parameter units; that defect is now fixed. It has not been
shown to account for all the failures in the saved study.

## The latest comparison

A 72-case study compared the original procedure with a longer one that revisited opposing
headings. It used fresh paired simulation inputs and the corrected calculation, and finished
in about nine minutes without fit failures.

The original procedure passed all 18 separation checks under one description of wind-related
uncertainty. Under the other, nine of 18 retained enough model separation and six also passed
the remaining scientific screens. The revised procedure passed none of its required separation
checks under either description. Neither procedure therefore passed the complete study.

The longer procedure had looked promising with known IMU orientation in a simplified calculation.
Its failure in the complete simulator shows why route calculations alone are insufficient.
A planned IMU turn also coincided with an aircraft turn. That is a timing problem to investigate,
not a demonstrated explanation for every failure.

## What the evidence does not establish

There are no completed real-IMU bench measurements in the current project work. Public flight
tracks supply positions, not IMU readings. The final decision thresholds have not been calibrated
and independently validated. No final wrong-rejection rate, broad usable-flight domain or
real-flight three-model conclusion has been established.

[Validation](VALIDATION.md) explains what comes next. The [technical validation record](VALIDATION_TECHNICAL.md)
contains the full campaign details. [Historical simulation tables](EVIDENCE_TECHNICAL.md) preserve
older results, with their original limitations; they are not current-release validation.

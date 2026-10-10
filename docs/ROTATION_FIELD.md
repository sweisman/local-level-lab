# Measuring the rotation field before interpreting its cause

## Purpose and status

This is a proposed follow-on to the current NASA airborne analysis, to begin after its
numerical work is complete and reviewed. It asks **what persistent rotation the original
IMU measurements support**, independently of choosing a physical explanation for it.
An **IMU (inertial measurement unit)** measures turning and acceleration. GPS records
position and motion over the ground. Survey-grade hardware makes slow rotation a credible
measurement target; this study will test the vector pattern rather than assume its rate.

This page records the scope and sequence. It introduces no code, fits or new campaign
allowance. The completed globe/flat comparisons and solver trial stay intact.
The [analysis roadmap](ANALYSIS_ROADMAP.md) adds the numerical, calibration-boundary,
absolute-fit and recording-dependence checks this estimator will also need. Exact device
characterization remains parallel work; it does not hold up development of the field estimator.

## What to measure

Represent the background field in local **north, east and down** directions. Begin with
three freely fitted coefficients, expressed in degrees/hour for reporting:

\[
\omega_N=A\cos\phi,\qquad \omega_E=B,\qquad \omega_D=C\sin\phi,
\]

where \(\phi\) is latitude. Do not impose \(A=-C\), set \(B=0\), or fix a rate near
15 degrees/hour. Those are relationships to test afterward. This particular latitude
form is itself a model; compare it with alternatives instead of calling it assumption-free.

The main questions are whether a nonzero field is needed, its vector direction and
magnitude, its variation with latitude and altitude, and its consistency across speeds,
headings, dates, flights and instrument configurations. Test globe transport separately:
turning caused by travel over a curved surface changes with trajectory, whereas a
geographically fixed background field should not depend on the aircraft's velocity.

## Separate measured rotation from aircraft motion

The gyro records rotation in its own axes. GPS ground track does not determine aircraft
roll, pitch or body heading; wind and maneuvers matter. Reconstruct orientation and motion
jointly from original gyro/acceleration increments and receiver observations, allowing
for mounting, calibration and timing errors. Accelerometers support that reconstruction;
the rotation field remains the measurement target. Applanix Group-1 fused attitude and
angular rates must not supply the independent observation or prescribe its background field.

Declare the geometry used to calculate transport rotation. Test its influence explicitly
where globe/flat remains unresolved. Keep frame-rotation and motion equations consistent;
do not hide a fixed standard Earth rate in orientation initialization or motion correction.
Conventional [inertial navigation uses prior Earth-rate and gravity information](https://docs.novatel.com/OEM7/Content/SPAN_Install/Fundamentals_of_GNSS_INS.htm),
which is precisely why the existing fused answer cannot perform this test for us.

Fit the field and instrument errors together rather than subtracting an assumed background
first. Use the same permitted errors in every field comparison. An arbitrary independent
gyro offset for every short stretch can absorb a background signal; quantify that ambiguity
before interpreting any fitted coefficients. Share calibration only within supported
instrument/installation epochs. Matching filenames or system identifiers is insufficient.

Unknown onboard Earth-rate subtraction creates another ambiguity: the recorded field
can be estimated, but a freely fitted original rate and subtraction amount may cancel
each other exactly. Report the **field retained in the logged measurements** first.
Infer a pre-correction field only where documentation or independent constraints separate
those quantities. Routine noise filtering and removal of a persistent signal are different
operations; neither the word "raw" nor a successful fit establishes the logging details.

## Competing field descriptions

Specify a small comparison set before new observed-data fitting:

| Description | Question it tests |
|---|---|
| Zero background | Can aircraft motion, transport and permitted instrument errors explain the recording without a persistent field? |
| Free latitude coefficients \(A,B,C\) | Do north/down components follow the proposed latitude pattern, and is there an east component? |
| One freely oriented vector in terrestrial Cartesian coordinates | Does one common geographic vector explain different latitudes and longitudes without imposing its axis? |
| Latitude-independent local vector | Does the direction remain constant in local north/east/down instead? |
| Purely vertical field | Is a north component actually needed? |
| Altitude-dependent extension | Is there an altitude trend after accounting for latitude, speed and instrument differences? |

A standard rotation-axis pattern is the restriction \(A=-C\), \(B=0\). Test that
restriction with magnitude fitted freely, rather than assuming it in the primary estimate.
Compare models using uncertainty-aware profiles and predictive performance on genuinely
held-out flights or installation groups. Extra field parameters must earn their complexity;
a lower training residual alone does not establish a better description.

## Work sequence

1. **Audit available coverage without gyro-based selection.** Reuse the saved eligible
   stretches and hashes. Tabulate latitude, longitude, altitude, speed, heading diversity,
   recorded IMU configuration and overlapping flight time. Establish which altitude and
   geographic comparisons the archive can actually support. Any broader selection needs
   a separately versioned motion/completeness policy, fixed before inspecting field outcomes.
2. **Build and test the field estimator separately.** Use the existing native-increment
   integration architecture in `analysis/lll/ilvis0_shape.py`, `ilvis0_forward.py` and
   `ilvis0_tangent.cpp` as references, preserving their frozen versions. Test known injected
   vectors, zero field, axis/sign transformations, transport-only motion, constant-offset
   ambiguity and unknown-subtraction ambiguity with cheap deterministic controls.
3. **Check separation before an observed trial.** Profile field coefficients against
   orientation, calibration, timing and transport freedoms. Report estimable combinations
   and unresolved directions. Near-polar latitude coverage can leave the north coefficient
   weakly constrained; high sample counts do not replace geographic diversity.
4. **Freeze a bounded trial.** Fix eligible identities, field models, error assumptions,
   validation split, stopping checks and a finite approved evaluation allowance. Reuse whole
   stretches; retain every failed or unfinished fit. Do not automatically expand the run.
5. **Report measured patterns.** Publish coefficient estimates, uncertainty, observable
   dependencies, cross-instrument agreement and held-out prediction errors. Avoid counting
   overlapping streams, repeated fits or short diagnostic sections as independent flights.
   Only then compare the measured pattern with proposed physical explanations.

The first implementation should establish the common vector and latitude pattern. Add
altitude, speed or date dependence only where coverage separates those effects. Sidereal
versus solar rate is a later precision question: their difference is about **0.041°/hour**.
Shared calibration and timing uncertainty must be small enough to resolve that difference;
more samples alone cannot remove a common offset.

## Interpretation

A reproducible field near \(A=+15.04\), \(B=0\), \(C=-15.04\) degrees/hour would
match the standard rotation-axis prediction in a specific, testable way. A different
pattern would need explanation and measurement-model checks. Failure to separate a
field from permitted instrument errors would be reported as a measurement limitation.

This experiment can distinguish explanations that predict different measurable fields.
Two explanations predicting exactly the same gyro, acceleration and GPS observations
cannot be distinguished by those observations alone. Measuring the field and identifying
its ultimate cause are therefore separate tasks.

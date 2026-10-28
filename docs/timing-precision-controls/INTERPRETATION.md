# Two numerical mechanisms reproduced

**Seven small controls passed.** They reproduce two mechanisms that can make
derivative checks disagree, without fitting another model or changing any
existing result. These are tests of the software arithmetic, not flight findings.

## Timing: a packet boundary has two slopes

The software predicts positions between successive IMU samples. In a turning
example, the approximation used inside one packet meets the next packet at the
same position, but their slopes differ. The analytic derivative follows the
ending packet. An inward test step from the lower time-offset bound enters the
next packet and follows its slope instead.

Both calculations agree with independently derived formulas for their own
branches. Shrinking the difference step does not make the two slopes agree.
The smooth, constant-acceleration controls pass, including at packet boundaries;
the boundary alone is not sufficient to create a discrepancy.

A hash-checked review of the four saved examples confirms the relevant timing
configuration: all have a **−0.01-second offset at its lower bound**, and **all
79 receiver queries land exactly at packet ends**. Their reconstructed interval
arrays match the previously saved hashes byte for byte. No inertial simulation
or residual calculation was repeated for this metadata check.

This makes branch choice a concrete explanation to test for the persistent
timing discrepancy. It does not establish its magnitude in the saved fits or
prove that it caused either stopping failure. Successful controls share the
same timing configuration.

## Precision: small changes can disappear beside a large coordinate

Two controls have identical motion and gyro-offset sensitivity; only their
longitude origin differs. At a zero origin, finite differences agree with the
analytic derivative to roughly machine precision. After adding one radian to
the origin, their relative error is 2.7% at the largest test step, and the two
smaller steps return zero sensitivity: a 100% error.

The analytic derivative remains unchanged and agrees with an independent
large-radius polynomial within about three parts per billion. The small
finite-radius correction stays in the native calculation. This isolates loss
of precision while accumulating absolute coordinates. Forming the final
residual before converting back to ordinary precision does not recover changes
already lost during accumulation.

These deliberately small, artificial fixtures expose the mechanisms; their
error sizes are not estimates for an aircraft recording.

## What this adds

The earlier four-point study found the patterns. These controls reproduce
specific reasons for them. A wider arithmetic type alone does not remove every
rounding limit, and an analytic derivative at a packet end need not match the
feasible inward slope used by a finite-difference test.

The next gate is a finite comparison at the same exposed saved points: measure
the branch-specific timing slopes and test a separately qualified approach to
coordinate accumulation. Keep all nuisance parameters, physical equations and
acceptance limits. Do not relabel the failed fits from these diagnostic results.
No replacement solver or fresh calibration campaign is qualified yet.

## Reproducibility

The 13 source-bound software tests and two reporting tests pass. The frozen
study uses one numerical thread, one charged compiler build, **49 native
evaluations and 2,212 conservatively counted packet-query visits**. All seven
tasks complete in 2.97 seconds, within their original allowances. No nonlinear
fits, new noise examples, aircraft reads or protected-data reads were performed.

The mathematical controls use short dyadic packet intervals and a large-radius
flat-coordinate limit to isolate the calculations. They are not new Earth-model
candidates, instrument specifications or a physical validation campaign.

[Summary CSV](results.csv) · [Frozen plan](PLAN.md) ·
[Earlier four-point diagnostic](../prediction-stopping-consistency/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).

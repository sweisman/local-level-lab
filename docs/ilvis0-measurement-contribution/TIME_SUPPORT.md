# Comparing the same measured time intervals

All **34 interval-association and prediction-bound checks pass**. These are
mathematical controls, with no original recordings or model fits. They address
two ways an acceleration-only comparison could accidentally compare different
quantities: uncertain synchronization and incomplete packet coverage.

An **IMU (inertial measurement unit)** records increments accumulated during
intervals. A packet timestamp does not, by itself, identify that interval's
duration or its alignment with the receiver clock.

## Whole packets, explicit clocks

The support helper takes explicit integration intervals under a named clock
hypothesis, receiver timestamps, a comparison window and bounds on one common
time offset. It does not infer physical integration periods from packet-header
differences. Nominal-period and header-period interpretations remain separate.

A packet is retained only if its entire integration interval lies inside the
window for **every allowed offset**. Boundary packets with uncertain membership
are listed separately. Receiver extrapolation and excessive receiver gaps reject
the comparison. Reversed, overlapping or zero-duration integration intervals
are rejected rather than repaired.

Packet gaps are preserved. For example, two retained intervals lasting 0.5 and
1.0 seconds with a gap between them provide 1.5 seconds of support. Neither the
gap nor the discarded boundary packets become measurements. Every candidate
must predict the average over that same interval union, using the same timing
allowance. No interpolation of scientific measurements is performed.

The current helper covers a **common clock offset**, not frequency error or
time-varying latency. Its integration intervals are exact under the supplied
hypothesis; uncertain physical durations need additional envelopes or separately
evaluated hypotheses. A support check does not calibrate the instrument clock.

## Bounding prediction averaging and synchronization

Let the predicted continuous force magnitude be \(q(t)\). Suppose a declared
bound \(L\) limits \(|dq/dt|\) over every packet's full possible time support.
For packet durations \(T_i\), midpoint evaluation differs from the continuous,
duration-weighted average by at most

\[
E_{\rm average}\leq L\frac{\sum_i T_i^2}{4\sum_i T_i}.
\]

Moving all intervals by an unknown common offset within \([a,b]\), relative to
a reference offset \(d\), adds at most

\[
E_{\rm sync}\leq L\max(|a-d|,|b-d|).
\]

The proof uses \(|q(t)-q(m_i)|\leq L|t-m_i|\) in each interval and integrates
the distance from its midpoint. No independence or statistical averaging is
assumed. Tests include an analytic tent function that reaches the averaging
bound, a linear history under several offsets, unequal packet durations and gaps.

These bounds concern the **predicted scalar force magnitude**. The separate
[direction-cone bound](FORCE_AVERAGING.md) concerns the loss of magnitude when
the measured body-force vector turns inside an IMU packet. Both effects matter.

## What remains before recording comparisons

The rate envelope \(L\), body-force direction envelope, integration hypotheses
and offset allowance need a declared, defensible common policy. An excluded gyro
or fused attitude cannot silently supply them. Receiver-derivative error,
trajectory truncation, calibration and nonlinear uncertainty are not included
in these time-support bounds. They still require a combined error budget before
the recorded-data comparison. No statistical coverage or new scientific decision
is established by passing these controls.

[Implementation](../../analysis/lll/ilvis0_common_support.py) ·
[Checks](../../analysis/tests/test_ilvis0_common_support.py) ·
[Contribution overview](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

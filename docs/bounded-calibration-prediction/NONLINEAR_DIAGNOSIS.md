# Saved numerical failure in the nonlinear check

The [24-case technical release](NONLINEAR_RESULT.md) completed every case. One
case, `sphere_rotating-1-increment-z_gyro_boundary`, did not pass the frozen
numerical stopping rule. Its generated flight used the specified-field globe,
processing case 1, the increment-noise law and a Z-gyro calibration at its
allowed boundary.

The fit stopped after 44 of 200 permitted evaluations with “no positive
predicted decrease.” Its fresh verification moved the objective upward by
0.0000179, a relative change of **9.16 × 10⁻⁸** against the unchanged
**1 × 10⁻⁸** limit. The fresh stationarity measure was **4.83 × 10⁻⁶**, below
its **1 × 10⁻⁴** limit. The largest change in a predicted receiver coordinate
under that verification step was below **0.0002 m**, below the **0.01 m**
position limit. Thus the relative-cost check is the failing component of the
saved stability probe; the optimizer's last proposed steps did not establish a
better feasible point.

A saved-Jacobian calculation makes the clock interaction concrete. The full
bounded local step has normalized length **0.096323**, of which the time-offset
coordinate contributes **−0.096275**. It predicts an objective reduction of
**0.00000711**, while the saved fresh evaluation increases the objective by
**0.0000179**. Holding time offset fixed leaves only a **0.00000000590**
predicted reduction. This locates the disagreement in the local timing
direction; it does not establish whether packet selection, derivative accuracy
or another nonlinear effect caused it. The check uses saved residuals and a
saved Jacobian, with no new flight fit or native prediction.

The saved training queries give a sharper timing check. At the fitted offset,
all **79** receiver epochs lie about **41.87 ns** after a 300 Hz packet end.
The proposed local time shift is **−0.000963 s** and changes the packet
assignment of **all 79** epochs. A reusable saved-only
`packet_assignment_change` check reproduces these counts from the sealed
training times and the frozen generated packet grid. The full linear step
therefore crosses a packet boundary at every training query. This is a
concrete reason to test the tangent within packet intervals before changing
the solver. The native tangent chooses a packet using query time plus offset,
then differentiates the fraction *within that packet*. A step crossing all
packet boundaries can therefore disagree with that local linear prediction
without proving that the derivative on either side is wrong.
In a separate two-second generated software control, the native time-offset
tangent agrees with finite differences taken wholly on each side of a 300 Hz
packet boundary, within **0.05 m per normalized parameter unit**. This checks
the local derivative on both branches; it does not qualify a step across the
boundary or resolve the saved failed fit.
A clean two-second cross-boundary check then found a maximum linearization
error of only **0.00000042 m**. Packet crossing alone is therefore not an
adequate explanation for the failed noisy, two-minute case. The interaction
with the longer trajectory and sensor noise remains to be isolated before
changing a solver rule.

The saved optimizer history narrows the problem further. This case accepted
12 steps and rejected 29; the final three proposed steps all failed to improve
the objective. The other three matched specified-field globe cases, varying
only noise input form or boundary calibration, passed their numerical checks
in eight evaluations each. All 239 frozen source files still match the current
checkout. This points to a specific noisy timing/calibration interaction, not
a generally broken native tangent. It does not establish the optimum or permit
relaxing the stopping rule.

The withheld prediction separately passes its declared accuracy screen:
**1.47 m** horizontal RMS and **0.76 m** vertical RMS. That does not promote
the fit to numerical qualification. The result remains a failed combined case,
and the study's existing allowance cannot be reused to improve it.

The [finite noisy timing probe](TIMING_PROBE_RESULT.md) subsequently saved eight
objective evaluations on this exact reconstructed case. With every other
parameter fixed, the full timing-only shift **increased** cost by 1.161831;
the local tangent predicted a 1.161805 increase. Values on both sides of the
packet boundary also tracked the tangent. This narrows the original failure
to the *joint* calibration/timing direction rather than packet switching
alone. The probe's wrapper closed terminal because it returned the abstention
field under the wrong key. Its sealed values are audited descriptively; the
terminal label and the original 23/24 gate remain unchanged. The next method
check must focus on the coupled direction, not repeat a broad timing sweep.
Qualify any solver change in an independently seeded control while keeping
the physical bounds and stopping requirements fixed.
Independent-seed interval coverage is a separate gate. The complete interval
containment in this development matrix is not a calibrated coverage claim.

[Per-case table](nonlinear-results.csv) · [Verified technical result](NONLINEAR_RESULT.md).

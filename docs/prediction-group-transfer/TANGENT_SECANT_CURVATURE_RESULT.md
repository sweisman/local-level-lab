# Trial-tangent curvature passes all eight generated controls

Reusing tangents from measured trials passed **8/8** generated
controls in **80 residual evaluations**, down from 262 with the
earlier weak-direction probes. The two weak cases passed in
15 and 17 calls, down from 34 and 33.

The saved calls include the initial tangent, every accepted and
rejected trial, and the unchanged fresh stopping checks. They
reconcile to **zero separate derivative probes**. The eight fits
record 41 curvature updates. The small controls still use their
known direct residual-change formula.

Eleven software checks passed. This qualifies the small generated
work only. The [native follow-up](TANGENT_SECANT_FLIGHT_PLAN.md)
uses standard native residuals and tests the full training and
withheld-forecast pipeline. No original or protected flight data
entered the small controls.

[Frozen plan](TANGENT_SECANT_CURVATURE_PLAN.md) ·
[Verified dispositions and charges](tangent-secant-curvature-result.json)

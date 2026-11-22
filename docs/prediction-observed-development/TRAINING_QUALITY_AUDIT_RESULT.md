# Receiver quality does not give a simple explanation for the height pattern

The [saved-only audit](TRAINING_QUALITY_AUDIT_PLAN.md) compared the two sealed
ESA fits' first 600 receiver reports with their fitted height errors. It
verified that each raw height difference is forecast height minus the saved
receiver height. No fit, later receiver report or reserved flight group was
opened. The two IMU error laws give practically identical associations.

| Saved training quantity | Raw height difference versus PDOP | Raw height difference versus satellite count |
|---|---:|---:|
| Ordinary correlation | +0.759 | −0.676 |
| Correlation of report-to-report changes | −0.286 | +0.219 |
| Correlation after removing a cubic time trend from each series | −0.328 | +0.417 |

The ordinary correlations reverse sign after either time check. The raw
height difference has 0.659 m RMS. The height error **after the declared
whitening** has a much weaker ordinary correlation with PDOP (−0.184), and
its cubic-time-adjusted correlation is +0.005. Its corresponding correlation
with reported height precision is only +0.031 after that adjustment.

PDOP ranges from 1.11 to 1.53, satellite count from 17 to 19 and reported
height standard deviation from 0.042 to 0.060 m in these saved rows. The
receiver reports vertical speeds from 1.64 to 4.65 m/s, so the interval
contains substantial climb motion. A shared time trend can make receiver
quality and fit error appear related even when their short-term changes do
not agree. Removing a cubic trend is a sensitivity check, not a physical
model of that climb.

This audit does **not** rule out receiver error. It shows that the saved
quality indicators alone do not provide a stable attribution for the
persistent fitted height residual. Motion, timing, calibration and error-law
misspecification remain possible. The [complete-fit generated pilot](FULL_FIT_INNOVATION_NULL_PLAN.md)
is running separately; aircraft forecast uncertainty is still unqualified.

[Saved numeric audit](training-quality-audit-result.json) ·
[Error-pattern audit](INNOVATION_MORPHOLOGY_RESULT.md)

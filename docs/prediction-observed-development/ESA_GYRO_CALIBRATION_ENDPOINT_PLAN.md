# Test explicit sensor corrections at the working allowance endpoints

Use the same sealed direction profiles and logged inertial intervals.
Recompute the measured force angles with each of the twelve bias
and gain terms set to its negative and positive existing allowance,
changing one term at a time. Apply the same correction to the observed
angles for both shapes. Retain the nominal angles and reproduce them.

For each receiver and averaging case, profile the corrected angles
against the frozen shapes and their retained fractions. A reversal is
established for this diagnostic if a tested disc score is smaller than
the lower bound across the entire globe fraction range. Also report
the corrected force-magnitude residual after an earlier constant
offset, using the saved scalar force predictions. Do not exclude an
endpoint based on that check.

Use one numerical thread and at most 25 inertial replays. Freeze the
exact code and inputs first. These are explicit measurement perturbations
within the previous bounds. The comparison leaves compatibility with
the full earlier position fit and the physical instrument unresolved.
No new Earth-model fit, later 120 reports or reserved group.

[Calibration bounds](ESA_GYRO_DIRECTION_CALIBRATION_PLAN.md)

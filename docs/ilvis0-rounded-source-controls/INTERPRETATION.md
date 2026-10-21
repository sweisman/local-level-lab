# The rounded adapter retains the saved training constraints

All **six generated-source comparisons passed** in 56.90 seconds. The study
verified all 36 training supports, fixed 120 body bounds, then completed all
1,440 known-calibration value and affine-error comparisons. No extra numerical
comparison margin was used.

The reference centers and all 27 supplied rows remain unchanged. The largest
calculated reference padding was about **1.0 × 10⁻¹⁶ m/s²**; it comes from center
and row arithmetic, not a relaxed sensor limit. Every existing nonlinear cap
remained sufficient. Known calibration values were read only after the selected
bounds were sealed.

This qualifies the rounded trained-source component on the declared generated
controls. It does not establish complete native propagation or useful position
prediction ranges. The older point failures remain preserved. No aircraft fit,
full native trajectory or protected ESA data was used.

[Evidence](README.md) · [Fixed scope](PLAN.md) · [Next gate](NEXT_PLAN.md).

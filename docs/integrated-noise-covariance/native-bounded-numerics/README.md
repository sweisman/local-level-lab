# Why two dense-reference checks failed

**Exact rational arithmetic identifies the dense reference whitening solve as the source of the discrepancies.** On the saved matrices, the general-purpose LU solve differs from the exact answer by 7.3–9.5 × 10⁻⁹. The triangular solve and structured calculation agree with it to about 10⁻¹⁴. Weak calibration directions amplify the former discrepancy into the 26–32 micrometre envelope mismatch.

Two separately charged captures reproduce and preserve both original failed assertions. Recalculating from their saved matrices needs no further native calls. Using a triangular solve in the dense reference meets the unchanged endpoint agreement tolerance on both captured cases.

The original 22/24 trial remains unqualified. The corrected reference needs a fresh full-matrix software qualification; no aircraft result, physical model, calibration bound or acceptance threshold changes. This also establishes no nonlinear coverage.

To reproduce the saved comparison, verify the captured NPZ hash, load it with `allow_pickle=False`, then call `lll.bounded_numerics.diagnose_saved_arrays` using the policy stored in the diagnosis report. The exact reference uses rational forward substitution on the original binary64 inputs.

[Capture plan](../BOUNDED_NUMERICS_PLAN.md) · [Original failed gate](../native-bounded-controls/README.md) · [Next analyses](../../NEXT_STEPS.md).

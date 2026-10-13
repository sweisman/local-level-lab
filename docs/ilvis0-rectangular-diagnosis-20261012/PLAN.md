# Saved-tangent diagnosis

## Purpose and scope

Identify why the completed rectangular-method trial failed qualification using only
its sealed summary, journals and saved local residual/Jacobian artifacts. There are
no original-data reads, native integrations, new archival fits or label changes.

## Implementation

1. Add `analysis/lll/ilvis0_rectangular_diagnosis.py` and focused tests in
   `analysis/tests/test_ilvis0_rectangular_diagnosis.py`. Validate saved arrays and
   hashes; report column scaling, weak directions, bound distances and trace behavior.
2. Compare unchanged and exact-bound starts on each saved affine residual model,
   with at most 200 evaluations per method and the same physical parameter box.
   Only coordinates within 1e-12 of ±1 move to the exact boundary. A bounded linear
   least-squares solve supplies a separate local reference. These calculations
   cannot test nonlinear trajectory behavior or qualify observational convergence.
3. Add `build_report.py` here. Preserve all 24 outcomes in CSV/JSON, publish a concise
   report and hash input artifacts, software and outputs. Keep the original trial
   and its source snapshots unchanged.
4. Test a known two-coordinate boundary stall, exact-bound recovery, rank deficiency,
   invalid inputs and corrupted artifact hashes; run the Python test suite.

## Interpretation limits

Near-bound snapping is a numerical hypothesis, not a new instrument calibration.
Success on a saved linear model does not recover a flight fit. Nonlinear derivatives,
receiver-time boundaries and perturbed-start behavior still require separate validation
before another observed-data trial. No evaluation allowance transfers from completed work.

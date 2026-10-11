# Full archival derivative check

**All 27 derivative columns passed for each of the three physical candidates.**
The three focused regression tests cover a rotating globe at −45°, a stationary
globe at +45° and the stationary disc at −45°, with roll and unequal packet spacing.
All 26 calibration/initialization/lever-arm/timing parameters and the profiled
Earth-rate-removal parameter are released for this check. No optimization is run.

The test evaluates a nonzero parameter vector and compares the native analytic
derivatives with separately evaluated changes in predicted position. It checks
each axis in metres per unit of normalized parameter, using absolute tolerance
0.00002 and relative tolerance 0.000002. Those tolerances were retained throughout.

The first two-point finite-difference probe at step 0.0001 failed on small north
responses: subtracting almost equal absolute latitude coordinates accumulated
round-off. A separate step sweep reproduced this for all three candidates. For
the first attitude column, north discrepancies fell from approximately 0.000075–
0.000088 to 0.0000008–0.0000024 when the step increased to 0.01. The larger step
also increased truncation error in other components, as expected.

The final test uses symmetric differences at steps 0.01 and 0.005 and fourth-order
Richardson extrapolation. The diagnostic north discrepancies remain about
0.0000021–0.0000033, while its east truncation error falls below 0.000000009.
All 81 column comparisons pass the unchanged criteria. This improves the independent
test, rather than altering the integration code or loosening acceptance limits.

The three tests passed in 42.08 seconds. Together with the earlier 38 tests,
**41 focused tests passed**. The new test is
`analysis/tests/test_ilvis0_compensation_full_tangent.py`; the completed latitude
study's frozen source files were not changed.

This establishes local derivative consistency. It does not establish unique
27-parameter calibration, a global optimum, correct archival preprocessing or
calibrated scientific significance. The [observed comparison proposal](OBSERVED_PLAN.md)
retains those distinctions and needs its own finite allowance.

# Turning reported rates into explicit candidate increments

The ESA iMAR files report angular rates and accelerations. They do not contain
the same original integer increments as the Applanix archive. A new streaming
adapter keeps the original samples and constructs candidate component integrals
under three explicit hypotheses:

| Hypothesis | Calculation on the interval between two timestamps |
|---|---|
| Left hold | Previous reported rate × actual elapsed time |
| Right hold | Current reported rate × actual elapsed time |
| Linear points | Mean of the two reported rates × actual elapsed time |

The [frozen qualification](../esa-rate-qualification/INTERPRETATION.md) now passes
all **48 generated identities**: 36 analytic quadrature cases and 12 local
body-rotation/force comparisons with independent ODE solutions. In addition,
**29 component tests pass**, covering constant and changing channels,
analytic integrals, derivative-bound error allowances, chunk continuation and
rejection of gaps, reversals and malformed support. The adapter preserves both
original rows, their timestamps and any declared alignment offset. It applies
no calibration, mounting, gravity or background-field correction.

These tests verify arithmetic and [local body bounds](BODY_BOUNDS.md) under
supplied sampling assumptions. They do not establish which assumption describes
the actual instrument or identify its filtering/coning/sculling processing.
Integrating the three rate components is not by itself an exact finite rotation
when the rotation axis changes. Geographic integration and accumulated recording
errors remain separate requirements before archive fits.

No ESA source recording was reread for these tests. No eligibility rule changed,
no model fit ran, and protected confirmation flights remain untouched. The first
receiver-only inventory still contains zero eligible stretches.

Implementation: `analysis/lll/airquantumgrav_increments.py`.
Tests: `analysis/tests/test_airquantumgrav_increments.py`.

[Qualification plan](PLAN.md) · [ESA selection](../esa-development-selection/README.md) ·
[Next analyses](../NEXT_STEPS.md) · [Technical roadmap](../ANALYSIS_ROADMAP.md).

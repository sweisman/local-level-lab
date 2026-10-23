# Preserve relationships between calibration parameters

The saved projection narrows only two individual parameter intervals. Repeating
the broad mounting-transform bound would therefore leave that allowance unchanged.
The next diagnostic should test the relationships between parameters directly.

The shared 51-column adapter now passes known-answer and wrong-reference checks.
A second check reconstructs the static calibration reference from verified start
fields, without loading the entire trajectory. Compatibility with the saved
long-history cases still needs its own finite diagnostic.

1. Reuse the checked static-calibration map in `lll.ilvis0_coupled_map` and its
   exact coupling-certificate audit. Its 24 shared error terms describe one
   calibration, not 24 independent adjustments. Build new certificates from the
   long-history reference; do not transplant a short-history source binding.
2. Add the necessary coupling constraints to the saved training region while
   retaining all 51 columns, all 30 training inequalities and the original limits.
   Qualify that adapter on known answers, wrong-reference rejection and unchanged
   feasible witnesses before using it for this diagnostic.
3. Compare the full box with a complete eight-part orientation cover. Preserve
   every part, including unsuccessful calculations. Numerical infeasibility alone
   must not discard a part of the physical domain. Freeze the finite map/support
   allowance and cost it before launch; this is a static saved-input calculation,
   with no trajectory integration or aircraft model fitting.
4. Assess whether the resulting constraints tighten acceleration or transform
   allowances enough to justify a separately frozen trajectory-bound test.
   Static success alone cannot qualify the long-history prediction ranges.

The original prediction-width targets and physical bounds stay fixed. The
aircraft observation-error model and full prediction-period coverage remain
separate requirements.

[Current diagnostic](README.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

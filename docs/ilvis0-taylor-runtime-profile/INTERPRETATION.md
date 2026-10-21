# Exact source-bound arithmetic is a measurable cost

Both shortened profiles completed. Source-body bounding takes 29% of profiled
propagation time. Its general affine-radius calculation takes about 12–13%,
and the additional derivative-based radius takes another 12%. These times
overlap their parent functions and must not be added to the parent totals.

Both operations repeatedly construct exact fractions from binary floating-point
inputs. Binary inputs have power-of-two denominators. Integer arithmetic can
represent their differences, products and sums exactly without reducing a new
general fraction at every step. The next implementation will test that change
against the existing exact-rational reference, including arbitrary centers,
all 27 columns, tiny values and nonbinary fallback inputs.

This is a proposed arithmetic optimization, not evidence that the timeout
problem is solved. Require identical outputs in component and native checks,
then measure a separate finite full-history screen. Preserve the completed
48-region comparison, its failures and the horizontal-width requirement.

[Measured profiles](README.md) ·
[Completed comparison](../ilvis0-taylor-complete-prediction/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

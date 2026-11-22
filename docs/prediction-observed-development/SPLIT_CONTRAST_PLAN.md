# Check a prediction test when earlier data choose its direction

Divide the observations into three fixed windows. Use the first to
choose a forecast contrast, the second to estimate calibration and
error scale, and the third to score the forecast. Form the windows
in chronological Gaussian innovations, which are independent under the
specified fixed law. The test on the chosen direction and the separate
error check on the rest of the path both include the uncertainty from
calibration in the second window.

Use 512 independently seeded generated histories with 18 reports in
each earlier window and 12 later reports. Use six affine calibration
parameters in a fixed design. For each history compare three scoring
conditions. Choose the direction from the independent first-window fit.
Repeat with a direction chosen from the same second-window fit that
estimates the forecast. Also score the independent split after adding
a separately generated calibration-shaped error only after the cut.
The first condition should place 91–99% of scores inside each nominal
95% reference band. The two stress cases should exceed the upper
contrast limit in at least 20% of the histories.

The generated offset is zero and the direction-selection rule amplifies
the earlier fitted parameter variation in the future design. This creates
a strong check of data reuse. The test does not establish what pattern
an aircraft will exhibit. Use one thread, at most 2,048 closed-form
coefficient evaluations, including direction selection, and 1,536
scores. No aircraft reading, physical-model fit or native call.

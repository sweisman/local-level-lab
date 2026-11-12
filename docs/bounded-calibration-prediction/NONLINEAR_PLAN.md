# Nonlinear aircraft check for the bound-aware interval

**Preparation only; no observed or generated fits are authorized by this file
alone.** The affine control and forecast adapter pass local checks. The next
question is whether their marginal intervals cover independently generated
aircraft positions when the fitted trajectory and calibration are nonlinear.

The technical release is fixed at seed **271828**, independent of the earlier
seed 71 pilot. Build it with all three physical candidates, both
upstream-processing cases, the independent-increment and shared-endpoint IMU
error laws, and both interior and declared boundary calibration: 24 generated
two-minute recordings at 300 Hz with 119 receiver epochs and the header-elapsed
clock. Fit each once with a 200-evaluation ceiling and explicit
physical bounds. Save the point forecast, both target-specific error operators
and bound-aware intervals **before** opening later physical truth or later
receiver reports. Retain all 26 or 27 calibration columns, actual packet times,
both error-law assumptions, every stopping failure and every charged start.
Do not select an error law from the nearly tied two-minute training scores.

Use a 2.5% calibration and 2.5% future-noise allowance in each marginal
interval. The four workers each reserve one numerical thread, with a 7,200 s
cooperative ceiling. Each task reserves at most 239,816 native calls and
1,506,051,012 packet visits, with zero bound calls/steps. Construction is
limited to 36,000 intervals, 36,199 generated samples and 649,206 normal
draws for increment truth or 433,212 for point truth. Charges are prepaid
before work; the task recovery route must pass before launch.

This release tests technical integration and the presence of nonlinear misses;
24 cases cannot establish a 95% coverage frequency. Before launch, freeze its
source and numerical environment hashes and recovery test. Qualify a generated known-answer
case and a dense independent conditional calculation. If the technical study
passes, prepare a separate independent-seed calibration/validation design for
empirical coverage across the complete candidate and calibration matrix.
Do not change limits or retry completed failed fits to make that result pass.

No NASA or ESA observed recording is fitted in this phase. Recording 187 and
all protected ESA confirmation groups remain outside the generated study.
The existing 53-stretch model preferences and the completed paired-law pilot
remain unchanged.

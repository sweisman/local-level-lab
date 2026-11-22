# Proposed observed optimizer comparison

This development pilot runs only if the separate
[longer independent-optimizer control](LONG_INDEPENDENT_SOLVER_PLAN.md) passes.
It tests whether two numerical methods reconstruct different withheld paths
from the same recorded IMU and earlier receiver observations. It does not
revise the original 80-fit study or its 50 nonpassing labels.

Select three of the already inventoried development recordings by metadata:
one northern 2010 stretch (ID `7df21c836bec5751f83c0cce`, 244 seconds),
one southern 2011 stretch (`2791235ca0b11b1ef4386e21`, 442 seconds), and
one southern 2015 stretch (`50f24131843071ae9312c082`, 554 seconds).
These choices span hemisphere, year and duration; they are not a random
sample or independent confirmation set. Reuse the sealed earlier-only inputs
and two receiver cuts from the original twenty-group study. Copy their bytes
with verified hashes; do not reselect intervals or read raw originals.

For each stretch and cut, run the custom trust-region solver and SciPy TRF
from zero and the same fixed perturbed start: **24 new charged fits**. Keep
the original specified-field globe, no-removal processing case,
header-elapsed clock, calibration box, receiver covariance, 200-evaluation
ceiling and original split. Save each continuous forecast before opening the
later receiver observations. Use four one-thread workers and finite
precharged native-call, packet-visit and cooperative wall limits. Prove
source/environment qualification, a separate real-worker preflight and
task-level reboot recovery before launch. Preserve every numerical failure.

Report each method's stopping result, training cost, physical calibration,
later north/east/height error and within-recording withheld-path spread.
Compare new paths with each other and with the sealed original paths without
altering their labels. A 0.1 m spread and 0.01 cost range are declared
diagnostic scales from generated development, **not** calibrated aircraft
acceptance limits. No Earth-model or statistical detection follows from this
single-candidate method study. The reserved ESA confirmation groups remain
unopened.

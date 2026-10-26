# The stopping failure repeats, and timing needs a closer check

**The four-point diagnostic is complete.** Repeating the calculations gives
exactly the same answers. The two successful controls still pass; the two failed
starts still fail. This rules out a changing answer between identical evaluations
as the explanation in these four examples.

The check also found small derivative discrepancies. A derivative tells the
solver how its prediction should change when a parameter moves. Those checks
need resolving before choosing a replacement solver or restarting calibration.
They occur in the successful controls too, so this diagnostic does **not** prove
that they caused the two failures.

## What happened at each saved point

| Saved example | Original fit | Repeated stopping check | Relative cost change |
|---|---|---|---:|
| Preceding noise example | Passed | Passed | 0.000000000000559 |
| Failing example, first start | Failed | Failed | 0.000000827373 |
| Failing example, second start | Failed | Failed | 0.000000827374 |
| Failing example, alternate processing assumption | Passed | Passed | 0.00000000000156 |

The unchanged limit is **0.00000001**. At both failed points, the local
approximation predicts a cost reduction of about 0.0000494. Recalculating the
proposed step instead increases the cost by about 0.000203. The resulting
position change stays below 0.5 mm, but the cost check still fails. A small
position change does not satisfy that separate numerical requirement.

The failed check moves about 0.22 in the normalized parameter vector, compared
with roughly 0.0000011 and 0.0000082 for the successful controls. These are
parameter-space distances, not metres or measured instrument errors.

## Two distinct derivative patterns

All 105 parameter columns were retained, including calibration and processing
parameters. Each was checked at three preselected step sizes.

- **Gyro Z offset:** smaller difference steps produce larger discrepancies.
  At the first failed point, the error rises from about 0.000000689 to
  0.00000417 to 0.0000505 as the step shrinks by factors of ten. That pattern is
  consistent with limited precision in the differenced calculation; it does
  not by itself establish that the analytic derivative is wrong.
- **Time offset:** the discrepancy stays nearly constant over the three step
  sizes. Its relative size ranges from about 0.0000073 to 0.000020 across the
  four points. This is a more specific reason to investigate the timing
  calculation and its derivative together.

At each of the two larger step sizes, 97 of 105 columns meet the predeclared
comparison scale. Gyro Z offset and time offset miss it in every example.
At the smallest step, 76 of 105 meet it. **None of the four points passes every
derivative comparison.** The comparison scale remains unchanged; these are
diagnostic results, not revised convergence decisions.

The frozen implementation deliberately preserves some calculations in ordinary
64-bit precision while evaluating others at wider precision. That is a concrete
place for the next software investigation, especially query timing and small
calibration changes. This study has not isolated a defective operation or
established a corrected implementation.

## Scope and accounting

The study used simulated measurements from four already exposed development
examples. It reconstructed the exact saved input arrays, parameter order and
costs. All 216 frozen source files remain unchanged.

The 32 software checks passed. Four native tasks completed in **35.2 minutes**,
using 646 residual-and-derivative evaluations. Accounting records 94,858 attempted
native operations and 1,202,098,014 packet-query visits. The larger prepaid
allowances remain charged: 239,816 operations and 1,506,051,012 visits.

There were **no nonlinear fits, new independent noise examples, aircraft-data
reads or protected-data reads**. The original fit labels and the 53-stretch
archive findings are unchanged. Calibration still supplies no validated
uncertainty threshold, and validation remains unstarted.

## Next gate

Resolve the timing and numerical-precision checks on small, independently known
problems before another solver comparison. Preserve the failed labels and the
current acceptance limits. A changed method needs a separately reviewed finite
phase; this diagnostic ends here.

[Verified diagnostic report](README.md) · [Summary CSV](results.csv) ·
[All derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·
[Previous phase outcome](../PREDICTION_PHASE_RESULTS.md) ·
[Next analyses](../NEXT_STEPS.md).

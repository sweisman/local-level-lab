# How much calibration would require

The [fresh-noise pilot](../independent-noisy-training-pilot/INTERPRETATION.md)
contains two independent noise seeds, despite its 48 fits. A calibration campaign
must count seeds, keep calibration and validation separate, and retain failed
fits. The [bookkeeping software](calibration-targets-qualification/README.md)
passes 30 source-bound checks, including separate calibration and validation targets.

Each new seed repeats 24 fits: both input formats, three generating/fitted
models, two processing cases and two starts. Its score is the worst of its
training-selected forecasts. These examples reuse the existing exact sample-size
calculations; neither is a launched campaign.

| Example | Calibration seeds | Validation seeds | Total fits | Estimated time with two workers |
|---|---:|---:|---:|---:|
| Minimum, requiring zero validation failures | 59 | 59 | 2,832 | 43 hours |
| Higher-power example, allowing four validation failures | 299 | 181 | 11,520 | 175 hours |

The minimum example can set a one-sided tolerance limit for 95% of its
generated score population at 95% confidence. Validation requires zero failures
to bound the failure rate below 5% at 95% confidence. Even if the actual failure
rate is only 1%, that validation has just a 55.3% chance of passing.

The higher-power example uses calibration aimed at 99% population coverage
with 95% confidence. Its separate validation tests the same 5% failure bound
at 95% confidence. It has 96.4% power if the true failure rate is 1%. These are
planning assumptions, not measured failure rates or confidence in an Earth model.

Runtime estimates scale the completed pilot's 43.8 minutes for two seeds and
two one-thread workers. Actual fit difficulty can differ. Four available workers
would roughly halve these estimates. Frozen execution needs its own conservative time and work
ceilings, not just these estimates.

Before either campaign, define the generating calibration values and geometry,
freeze the common population hash and disjoint seeds, and qualify its execution
adapter. A finite set of calibration examples does not certify every parameter
value inside the permitted bounds. No aircraft fit or protected ESA group is
released by these calculations.

[Execution design](EXECUTION_PLAN.md) · [Calibration method](CALIBRATION_PLAN.md) ·
[Next analyses](../NEXT_STEPS.md).

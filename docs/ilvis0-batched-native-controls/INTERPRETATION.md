# Faster interface, identical checked results

All **24 native controls passed**. Every one of the **348 prediction bounds**
exactly matches its sealed predecessor, including point predictions, error
allowances, all three coefficient matrices and physical-domain bindings.

The study completed in 91.75 seconds with four single-thread workers. The
predecessor used the same allocation and took 201.31 seconds. These are recorded
study runtimes, not a guarantee for long recordings.

The change combines repeated interface calls. It does not change the physical
models, calibration caps, source rounding allowances or acceptance limits.
Floating-point mode and invalid-input rejection remain checked.

The next gate is a separate six-source long-history screen under the original
time limits. The complete prediction-width target remains four of six groups;
no aircraft fit or finding changes.

[Results](README.md) · [Frozen scope](PLAN.md) ·
[Long-history plan](../ilvis0-batched-range-preflight/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

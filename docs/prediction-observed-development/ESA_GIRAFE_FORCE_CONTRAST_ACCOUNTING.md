# Record each force average separately

The first force-contrast run stopped before any force evaluation.
The shared ledger rejected its request to charge a batch of 128 force
averages as a single numerical operation. All eight failed task
records are retained under `data/esa-girafe-force-contrast-v1`.

The separate v2 run copies the exact sealed inputs from v1 and keeps
the same scientific plan, windows and limits. Charge one bound call and
its 40 or 96 quadrature points before each force average. Freeze the
accounting regression test alongside the variant. The limit is 6,144
force averages and 417,792 quadrature points, with one thread and
a three-minute ceiling. Each failed first-run task remains recorded.
No calibration bound, score or data selection changes.

[Original design](ESA_GIRAFE_FORCE_CONTRAST_PLAN.md)

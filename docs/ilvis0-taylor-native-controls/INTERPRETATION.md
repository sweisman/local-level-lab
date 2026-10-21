# Source derivatives preserve the checked native calculation

All **24 native controls pass**. Across all **348 bounds**, point predictions,
coefficient matrices and physical/reference bindings match the sealed
predecessor exactly. None of the checked unshared error allowances widens.

The new calculation intersects a source-specific mean-value remainder with
the existing physical and training bounds. It accounts for numerical center
and row differences explicitly, retains the clock direction and keeps all 51
physical/shared columns. No calibration cap or acceptance tolerance changes.

The study used 78 native evaluations, 60,288 logical bound steps and four
single-thread workers, completing in 129.67 seconds. These are generated
software controls, with no aircraft observations or protected ESA data.

The next gate is the separately frozen six-source long-history comparison.
Useful complete prediction ranges and observational confidence remain open.

[Results](README.md) · [Frozen scope](PLAN.md) ·
[Long-history plan](../ilvis0-taylor-range-preflight/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

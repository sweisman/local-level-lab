# Matched saved-matrix check of feasible initialization

The independent convex controls reproduce ten failures in 24 cases under the
previous linear calculation. Starting BVLS at the feasible zero step passes
all 24; a separate 26-column problem checks that the method also moves from a
nonoptimal start. A post-solve check rejects worsening results even if SciPy
reports success. The feasible box, columns and acceptance limits stay fixed.

This uses SciPy's version-bound BVLS core to supply the initial point explicitly;
the public wrapper does not expose that argument. Qualification records the
numerical environment. A dependency update requires requalification.

## Separate finite comparison

Use the exact four saved final-baseline matrices selected in the
[earlier diagnosis](timing-linear-baseline-diagnosis/README.md): both failed
starts and the matched earlier control pair. This is a new method and allowance,
not a restart of the closed four-case study. Its result-schema rejection stays
preserved. No original fit labels change.

Freeze four starts, four charged bounded linear solves, one numerical thread,
600 seconds cooperative, zero native calls and zero nonlinear fits. Bind the
source, environment, selected fit hashes and parent completion before launch.
Run the independent controls and shared-finish schema test before freezing.

Recompute linear costs independently. Require all columns and bounds, feasible
proposals, solver success and nonworsening objectives. Preserve every outcome.
Using a saved final linearization is not an exact native replay at a different
timing-cell anchor. Even a successful outcome qualifies only this linear check;
full optimizer qualification and a separately frozen native trial must follow
before a new calibration campaign.

[Current roadmap](ANALYSIS_ROADMAP.md) · [Known-answer controls](TIMING_LINEAR_SOLVER_CONTROLS.md).

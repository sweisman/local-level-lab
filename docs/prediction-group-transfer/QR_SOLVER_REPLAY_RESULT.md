# Both direct bounded solves recover the seven known linear targets

The direct and QR-reduced bounded least-squares methods each passed all
seven controls, including the unchanged fresh-position check. These are
the same saved derivatives and known targets on which the two iterative
centered solvers had passed zero of seven. All 26 calibration directions
and the original bounds were retained. [Frozen plan](QR_SOLVER_REPLAY_PLAN.md) ·
[Previous scaling result](SCALED_SOLVER_REPLAY_RESULT.md)

| Method | Passing cases | Largest error from the known prediction, whitened units | Rows in the bounded solve |
| --- | ---: | ---: | ---: |
| Direct bounded least squares | 7 of 7 | 1.41 × 10⁻¹⁰ | 48 or 240 |
| QR-reduced bounded least squares | 7 of 7 | 6.08 × 10⁻¹¹ | 26 |

Both errors are below the frozen limit of 0.0001. The controls reached
between five and twelve parameter bounds, depending on the case. The
QR reduction took fewer rows into the bounded solve. This check establishes
accuracy on the known linear problems. Whole-fit speed and convergence
along a curved aircraft path still need qualification.
The solver already used for observed ESA fits does direct bounded linear
corrections, so the two unresolved ESA settings retain their status.
[Observed stopping evidence](../prediction-observed-development/ESA_400_120_MODEL_MATRIX_STOPPING.md)

All 63 charged operations completed on one numerical thread. No native
trajectory calculation or reserved data was used. Four focused tests passed.
Result SHA-256 `b14536cd579dd8a759173d5d7dd815f1a8a5d6d6ec765717ab5ce28ddbdc05cf`.
[Machine-readable result](qr-solver-replay-result.json) ·
[Frozen execution evidence](qr-solver-replay-evidence/README.md)

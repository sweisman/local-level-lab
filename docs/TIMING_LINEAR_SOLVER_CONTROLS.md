# Known-answer checks for the bounded linear solver

The saved-baseline diagnosis reproduces a worsening linear proposal despite a
feasible zero step. Before changing the implementation, test whether the same
failure occurs on an independently constructed convex problem.

Use 24 deterministic software controls: 4 or 26 columns, two large-column
scales, three weak-column scales, and full or one-ULP timing bounds. Construct
the matrices from a binary Hadamard matrix and powers of two. Set a feasible
corner point from the exact gradient signs, so the first-order box conditions
prove it is a global minimum of the convex quadratic. No aircraft inputs,
generated IMU histories, stochastic draws or native integrator calls are used.

The first check permits one current bounded solve per control, at most 100
iterations each. Preserve every failing case and solver status. The unchanged
linear equation and independent scalar cost comparison must agree. A correction
must retain every column and the original feasible box; changing the feasible
set or dropping weak directions is not a remedy.

These ordinary local software checks neither repeat a closed study nor qualify
aircraft inference. Any later method qualification, native trial or calibration
needs its own source freeze and finite allowance.

[Saved diagnosis](timing-linear-baseline-diagnosis/README.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).

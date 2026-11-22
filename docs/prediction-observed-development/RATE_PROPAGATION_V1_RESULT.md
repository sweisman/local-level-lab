# First fixed-parameter rate comparison: technical failure

The three tasks on ESA development recording 187 finished, with **3/3 native
calls charged** and no refits. The original linear-point trajectory failed
the predeclared exact-reproduction check. Its largest difference from the
sealed forecast was **0.0000145 m in height**; latitude and longitude differed
by at most 4.6×10⁻¹⁴ and 2.8×10⁻¹³ radians. The tolerance was 10⁻¹² in each
stored coordinate, so the study is **terminal and unqualified**. The left and
right trajectories were saved, but their outcomes cannot pass this study's
baseline gate and are not used to choose an integration convention.

The compilation receipts identify the likely reason: this study called the
ordinary binary64 tangent kernel, whereas the sealed original forecast used
the repository's extended-precision residual tangent kernel. The underlying
native equations and compiler are the same, but the generated binaries differ.
That explains the scale and vertical growth of the discrepancy; it remains a
diagnosis, not a retroactive pass. The original task results and charges remain
unchanged.

A separate, newly frozen study must use the original extended-precision kernel
and first reproduce the sealed forecast under the original strict tolerance.
Only then can the left/right position sensitivities be interpreted. No
protected confirmation flight was opened.

The sealed study manifest is
`2162c1ed5fb8f8b39eb5e8ce93dabe15cf369746b2c4e81680ec5e44bfca4dce`;
its summary is
`d57aeff8f6111b96fac79d3c1f222bad2be244795b05e00ff02e2ca6c03d3c01`.

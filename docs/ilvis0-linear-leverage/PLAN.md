# Saved linear training-leverage diagnostic

Use only the first two predeclared, sealed generated cases of the long-record
study. Read their saved physical Jacobians at five training epochs and the
438-second prediction. Do not read aircraft originals or evaluate native motion.

Retain all 27 physical directions and their original normalized ±1 box. Treat
the saved linear training changes as constrained to ±1 m per coordinate. Omit
shared errors and nonlinear remainders explicitly: this is an optimistic
affine geometry diagnostic, not a physical prediction or confidence interval.

Each of two identities reserves six LP proposals: positive and negative future
change on each axis. Each proposal has a five-second solver limit. Verify its
primal point exactly using rational arithmetic; if represented feasibility
needs repair, contract all coordinates by one common factor. Save the points,
training changes, contraction and future changes. These establish feasible
affine spreads, not exact LP optima or nonlinear feasibility.

Freeze source, inputs and environment. Use one numerical worker/thread while
reserving three for the two active studies. Cooperative wall limit: 120 seconds.
Maximum: twelve proposals, zero native calls, bounds, packet visits or observed
model-fit starts. No retries, process signals or allowance changes. Preserve
failed identities. Render the final report only from sealed results.

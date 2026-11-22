# Saved weak-direction audit

Question: Which normalized nuisance combinations are least constrained by the
earlier receiver observations in the completed generated study?

Use the twelve sealed fits whose physical candidate matches the generating
model. Each fit saves its whitened training Jacobian and singular values.
Independently recompute the singular-value decomposition; reject a mismatch
with the saved values. Record the weakest right-singular vector's absolute
loadings, the ratio of weakest to strongest singular value, and the three
largest loadings for every fit. Summarize how often each parameter appears
among those three. The vector's sign is arbitrary, so use magnitudes.

This is a local linear training diagnostic. It does not allocate the later
forecast width uniquely to parameters, prove a hardware error, narrow the
calibration box or make an Earth-model decision. It runs no new fits.

# Bound the ESA forecast with the calibration terms linked

Recheck the nine surviving high-bound ranges on development recording
187 using the saved earlier GPS constraint and the same signed forecast
score. Use only the original squared-loss increase limit of 0.01 and
the zero earlier unshared error sensitivity case. Keep the old bound
for every range unless a verified tighter bound applies.

Project the loss constraint onto the saved feasibility direction and
the saved child score direction for each range. Apply each projection
once directly and once with its saved linear cuts after dropping cuts
that use separately lifted products. Evaluate what remains using one
static calibration for all terms. In particular, acceleration and its
force transform share a matrix. Collect their coefficients before
taking the interval. Exact coefficient intervals, the outward rotation
series and the existing static map allowance cover arithmetic in the
bound under the same premises as the original map. This does not
certify the full integrating calculation or establish aircraft coverage.

For a range to be excluded, the upper bound on zero under the necessary
earlier loss constraint must be strictly negative. Check that any
retained, verified linked point in that range survives the calculation.
Report every bound, and recombine across the original complete cover.
Compare the two candidates' combined bound with their 25.41-unit nominal
separation. A wide bound is an inconclusive result.

Use two one-thread tasks with four directional bounds per range and a
120-second cooperative wall allowance. Start no trajectory fits, read
no later receiver positions and use no reserved flights.

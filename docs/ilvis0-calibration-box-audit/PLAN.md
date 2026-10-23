# Can training narrow the calibration box?

Use the six completed generated-data cases from the full-history prediction
test. Verify their saved result and training-region hashes. Project each of the
27 physical parameters while retaining all 51 physical and shared coordinates,
every training inequality and the original calibration limits.

Each signed coordinate bound needs a numerical proposal and an independently
checked exact certificate. A failed proposal retains the original box. Narrower
coordinate intervals do not replace the coupled constraints or establish that
every point in their Cartesian product is feasible.

Limits: six identities, one numerical thread, 600 cooperative seconds, no retries;
54 proposals and 162 exact checks per identity, totaling 324 and 972. Each proposal
has the shared one-second solver limit. Charge before execution in indexed
journals. There are zero native calls, new trajectory bounds, aircraft reads or
model fits. Preserve the earlier unsuccessful prediction ranges and abstention.

The result determines whether a safely narrowed parameter box is worth testing
in a separately frozen position calculation. It cannot qualify prediction
accuracy or an aircraft error model.

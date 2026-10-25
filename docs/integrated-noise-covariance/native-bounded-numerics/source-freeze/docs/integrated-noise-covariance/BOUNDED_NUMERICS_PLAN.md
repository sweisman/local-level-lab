# Diagnose the two bounded-envelope numerical discrepancies

The [completed native gate](native-bounded-controls/README.md) passes 22 of 24
cases. Two sampled-rate disc cases disagree with the dense reference by
26–32 micrometres at a height-envelope endpoint. The gate remains unqualified;
its tolerance and outcomes are fixed.

The failed run retained errors and charges, but not the intermediate matrices.
This separately charged diagnostic repeats the supplied native calculations for
only those two configurations, solely to preserve that numerical state. It
performs no fitting and does not add qualification attempts or change a verdict.
The original test body is loaded with its verified source hash. Recording
wrappers preserve its calculations, capture its arrays and retain the original
assertion outcome. They do not suppress a failure to make the gate pass.

Save the full innovation factor, raw forecast derivatives and earlier residual,
both whitened designs, coefficient bounds, singular values/bases, conditional
contrasts and parameter-support endpoints. Then compare the arithmetic from
those saved matrices without more native calls. Investigate coordinate scaling,
conditional-covariance subtraction and weak singular directions separately.
Do not presume the dense reference or the structured implementation is correct.

One numerical thread, two compiled libraries and a three-minute cooperative
allowance are permitted. Each of the two cases is capped at 450 native calls,
15,000 packet steps and 300,000 packet/query visits. Totals are 900 calls,
30,000 steps and 600,000 visits. Save at most 1 MiB of arrays per case, excluding
compiled artifacts. All work is prepaid; unused allowance is not returned.
There are no optimizer starts, noise draws or original/protected data reads.

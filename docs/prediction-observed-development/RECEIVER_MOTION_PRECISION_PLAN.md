# Check the precision of receiver-derived motion proxies

Use the same three sealed training selections on ESA recording 187.
Decode only their 2,400 training receiver reports and verify the full
source hash in one pass. Read the reported north/east/up velocity
covariance and convert it to the conditional precision of course and
flight-path angle. These are directions of motion, not body attitude.

Use centered 30- and 120-second ordinary least-squares slopes on the
original one-second queries. Propagate the reported marginal covariance
to the rates under two cases. One assumes independent errors across
epochs. The other gives a standard-deviation upper bound for any
cross-epoch correlation consistent with the reported marginal variances.
Neither case estimates the actual cross-epoch correlation.

Compare these precision scales with the previously saved rate gaps.
For equal RMS motion allowances on the two candidate paths, two
allowances equal to half the gap can bring them into contact. Use the
same coordinates and time support to interpret this deterministic
budget. The receiver slope uncertainties refer to individual smoothed
directions and only give a scale comparison with that budget. Aircraft
yaw, pitch and roll need independent evidence beyond these proxies.

Use one thread, one source pass, 64,080 source row identities, 2,400
decoded training reports and six two-axis slope summaries. Read no
IMU or later scoring positions and make no fit. All reserved groups
remain closed.

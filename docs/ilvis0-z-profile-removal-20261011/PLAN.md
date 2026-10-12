# Matched processing-assumption grid

Version `ilvis0-joint-z-profile-followup-v1`, study `removal`.
Target `570b37d23af5e245dd461051`: the complete, previously selected 438-second
IMU21 stretch, median speed 878.06 km/h, minimum 859.55 km/h. Reuse its sealed
selection and reference; preserve previous results.

Exact grid: Z gain {−2%, 0, +2%} × constant Z offset {−1, 0, +1 degree/hour}
× {specified-field globe, zero-field globe, stationary disc}, yielding 27 identities.
Use only `bias1_profiled_removal`, with the existing common upstream removal fraction in
[0, 1]. Keep original integration, packet-header intervals, physical bounds and
the original fitter. Free normalized coordinates start at zero; removal starts at
zero (normalized −1), followed by the frozen initialization stages. Fixed Z
coordinates cannot move.

Allow one start per identity, at most 200 native sweeps/start and 5,400 total,
no retries or reserve. Count derivatives and both final predictions. The nominal-clock
prediction holds fitted parameters fixed; it is not a reoptimized clock comparison.
One worker, two threads. No further clock grid or archive rollout is included.

Save costs, convergence, feasible stationarity, full/free derivatives, singular vectors,
remaining boundaries and both clock-error diagnostics. Report shape first, then field
only after all intended shape comparisons converge and favor globe. Unfinished nodes
cannot complete a profile minimum. Grid nodes are not confidence contours or factory
calibration estimates. Preserve integer measurements, source/input/environment hashes
and kernel metadata. Charge durably before each start; never retry interruptions or
resume after completion.

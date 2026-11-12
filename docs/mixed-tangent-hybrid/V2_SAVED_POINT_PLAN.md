# Revised fast tangent: saved-point gate

Question: does widening the two weak attitude columns materially reduce the
derivative differences found at the six saved ESA development fit points?
This is a numerical method check, not a new Earth-model fit or decision.

Use exactly the three failed pairs and both saved points per pair from the
sealed `esa-same-point-tangent-20261111-v2` study. Reuse its verified earlier
IMU prefix, receiver observations, parameter vectors and wide-reference
tangents. Evaluate the revised tangent once at each point: **six charged native
calls**, at most 800 × 239,867 packet visits per call. Use three workers with
one numerical thread each, a one-hour wall limit and no optimizer starts,
original-file reads or protected ESA reads. Preserve all failures. Freeze the
input, implementation and numerical environment hashes before running.

Require values to match the wide reference bitwise and timing-boundary counts
to match. The development gate for a later paired-fit test is: at every saved
point, the largest derivative difference is at most one tenth of the original
hybrid difference, and each of the two attitude-column differences is below
10⁻⁸ metres per normalized parameter unit. If either condition fails, stop
this revision; do not relax it or rerun these points under a new threshold.
Passing this gate would justify a separately frozen paired-fit check, not
qualify observed-data substitution or change the 21/24 historical result.

Use the existing task-level recovery mechanism: completed failures remain
sealed, unfinished technical work requires a separate finite continuation,
and original charges are never reset. Do not launch without a verified
interruption-recovery path.

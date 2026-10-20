# Finite joint-affine support qualification

Qualify exact support certificates before connecting them to native prediction
bounds. The mathematical inequality and next dependency are described in the
[joint calibration plan](../ilvis0-native-training-contraction/JOINT_PLAN.md).

Freeze **24 generated identities**: twelve two-dimensional polygons checked by
independent exact enumeration of all feasible vertices, eight 27-coordinate
systems with two equal correlated coordinates and twenty-five wholly
unidentified coordinates, and four weak-constraint/full-box fallbacks. Check
both objective signs and deliberately poor nonnegative multiplier proposals.

Keep every nuisance column. Every returned bound must contain the exact known
optimum; every declared feasible vertex remains represented. In the correlated
systems, the difference of the first two coordinates must vanish while all
unidentified contributions remain. LP failure or nonfinite multiplier proposals
must fall back to a verified full-box certificate, never an empty region.
Unit controls cover those failure statuses and outward overflow separately.

Limits: at most **144 certificates, 48 LP proposals, 60 cooperative seconds**,
four reserved numerical threads in one worker, and one thread/one cooperative
second for each LP proposal. Reserve six certificates and two proposals per
identity before calculation. There are zero native evaluations, optimizer starts
on aircraft measurements, original-file reads or ESA evaluations. No retries,
extensions or process signals. Freeze sources and environment before launch.

A pass qualifies only the mathematical support calculation. Training
inequalities, nonlinear remainder bounds and measurement assumptions remain
separate requirements. No observational fit follows. The next stage needs a
new finite generated freeze covering the full original orientation range;
this study does not narrow that range or spend any previous allowance.

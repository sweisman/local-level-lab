# Why the horizontal software gate failed

All four failed flat-model fits reach stationary endpoints with horizontal
errors below three nanometres on this short generated trajectory. The fresh
local probes nevertheless increase normalized squared error from roughly
1e-13 to 1e-7 and fail stationarity. This is a numerical qualification failure,
not evidence that flat or globe describes real observations better.

The saved affine systems retain 26/27 columns but have ranks 23/24. The existing
bounded correction proposes maximum-size 0.001 moves in several weakly
constrained calibration and timing coordinates. The linear approximation
predicts improvement; the saved nonlinear evaluation instead worsens the cost.
Simply rescaling columns also reaches those step limits.

A diagnostic ridge penalty of 1e-6 in column-scaled displacement produces
maximum normalized steps of about 1.1e-6 to 2.1e-6 on the same four endpoints.
It retains every column and the original feasible physical region. Its
prediction is promising, but no saved affine calculation proves that the
actual integrated trajectory improves or remains stable. The separate native
probe checks that question before any candidate qualification.

There is a second issue: the two zero-field globe starts under the unsubtracted
processing case finish at objective values differing by about 2.17e-8, above
the frozen 1e-8 repeatability limit. Their predictions differ by less than
0.6 micrometres. A probe modification alone does not establish that the fitting
algorithm can reproduce the same objective from different starts.

The next software method must address both correction behavior and paired-start
repeatability. Earlier failures remain failed. None of this changes the
completed 53-stretch recorded-data comparison or calibrates its significance.

[Saved-array results](README.md) · [Native probe scope](../ilvis0-horizontal-probe-20261018/PLAN.md).

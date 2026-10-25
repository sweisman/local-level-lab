# Short native bounded-uncertainty controls

This finite software test follows the separately qualified native-interface
checks. It evaluates supplied calibration points; it performs no optimization.
It does not repeat the completed two-minute fitting study.

The matrix has 24 cases: both input-error laws, three candidates, both processing
assumptions, and constant versus height-dependent gravity. Each uses a generated
160-packet record with 12 receiver query times. Only the first ten receiver
positions enter initialization and error conditioning. A supplied gyro-offset
parameter is exactly at a bound. All 26/27 mean columns remain present.

Compare the returned bounded envelope with a separate dense calculation from the
same fixed covariance. Verify its conditional mean, every parameter contrast,
shared-error response norms and error allocation. Preserve the original
unrestricted diagnostic's boundary abstention. No future receiver observations
are passed to the provider.

The zero mean-remainder allowance here tests the **linearized mathematical
problem only**. This does not bound the nonlinear native map or establish
physical truth coverage. A second calculation with missing nonlinear allowances
must explicitly remain unsupported. Do not refit any failed case.

Before compilation, freeze all sources and the environment in a fresh request.
Use the shared prepaid test fixtures with one numerical thread and a three-minute
cooperative wall limit. Allow two compiled libraries in total. Each case permits
at most 450 native calls, 15,000 packet steps and 300,000 packet/query visits.
Totals are 10,800 calls, 360,000 steps and 7,200,000 visits; unused prepayment is
not returned. There are zero optimizer starts, noise draws, original-recording
reads and protected-data reads. All failed checks and journals are retained.

# All seven reserved slices support the development forecast cadence

The development analysis used every other report from the 2 Hz receiver
export. At that cadence, **all seven reserved slices can supply 400 or
800 training reports and the same 120 withheld reports**. The shorter
and longer training layouts span about 399 and 799 seconds. The withheld
reports span about 119 seconds.

The largest gap was 0.500002 seconds between original reports and
1.000003 seconds between selected queries, both rounded up.
The last query left more than 279 seconds of verified inertial timing
support in every slice. All seven complete receiver files matched their
acquisition hashes. The check decoded only receiver sequence numbers,
GPS weeks and timestamps. It opened zero raw inertial values and ran zero
fits.

This check uses the prediction cadence from the development fits. The
[earlier check](ESA_CONFIRMATION_QUERY_RESULT.md) used every half-second
receiver report, so it covered half as much time for the same report
counts. The checked placement here tests whether both training lengths
can be compared against identical later observations. The final time
selection and decision policy remain to be frozen.

The [earlier receiver profile](ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md)
compares satellite geometry and motion on these same layouts. It keeps
the later positions and inertial readings protected.

[Fixed plan and commands](ESA_CONFIRMATION_CADENCE_PLAN.md) ·
[Exact indices and time hashes](esa-confirmation-queries-v2-result.json) ·
[Source and environment bindings](esa-confirmation-queries-v2-freeze.json).

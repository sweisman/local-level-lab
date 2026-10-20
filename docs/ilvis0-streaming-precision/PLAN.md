# Isolating long-record arithmetic from chunking

The first streaming study passed all 42 short reference/pose controls but failed
a 400-second exact-pose tolerance. Its failure, three unstarted identities and
remaining allowance stay sealed. This separate study changes no kernel, source
data, model, fitted parameter or tolerance.

Four controls compare the same 120,000- and 480,000-packet, nominal-300-Hz
specified-field inputs with the unchanged whole-array kernels, in both value
and 27-column tangent modes. They report each calculation's exact-pose error
separately from the streaming-minus-reference error. This directly tests whether
the earlier discrepancy was introduced by chunking. It cannot turn an inherited
precision error into a successful exact-pose result.

Two independent 480,000-packet controls use exactly representable arithmetic:
zero angular increments, a zero-field globe, 1/256-second periods and gravity
9.75 m/s² with matching velocity increments. The exact solution is a stationary
pose. Both value and tangent calculations must remain within the unchanged
1-micrometre absolute criterion.

The reference comparisons retain 1 micrometre for position differences and
1e-7 metres per normalized parameter for every derivative. A checkpoint at a
mid-record block boundary must preserve the output. All boundary counts must
agree. No adverse result may be dropped or retried.

The finite allowance is six generated identities, 4,500 native calls,
4,000,000 packet visits, 1,024 packets per streaming block, four total numerical
threads and 300 cooperative wall seconds. Calls/packet visits are charged before
execution; no signals enforce time limits. An interrupted start stays charged.

Reference arrays are allowed for equivalence testing only. During the streamed
phase, query results are compared and discarded blockwise; the traced working
allocation must remain below the unchanged 8 MiB ceiling. Reference storage and
shared-library/compiler storage are reported as outside that measurement.

Passing software equivalence does not establish whole-record physical accuracy,
an absolute floating-point enclosure, calibrated uncertainty, observed-data
continuity or ESA predictive adequacy. Archive fits remain blocked by their
separate scientific gates.

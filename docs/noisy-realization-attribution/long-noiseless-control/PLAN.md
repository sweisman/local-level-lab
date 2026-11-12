# Full-length noise-free oracle control

Test whether the same known-correction predictor used by the six-stream
diagnostic can follow its generating trajectory over the full twenty minutes
without sensor or receiver noise. This is a software development check, not an
observed-aircraft fit or a new Earth-model comparison.

Use one preselected case: rotating globe, zero upstream removal, 55° latitude,
the parent's fast course pattern, climb height profile and inverse-square
gravity. Generate 360,000 ideal IMU increments at 300 Hz and query the 1,200
receiver times from 0.5 to 1,199.5 seconds. Supply the generating calibration
and starting state. Score against the noiseless generating receiver positions.
The physical acceptance limit is the existing 10 m later horizontal RMS and
30 m later height RMS; also report the first, training-boundary and final
horizontal errors. A failure is retained as a diagnostic result, not repaired
by changing the threshold or shortening the history.

This check permits one native value forecast, at most 432,000,000 packet/query
visits, one numerical thread and no optimizer start. A source/environment
request is recorded before execution. The local test report and result are
retained. The test uses shared library components; it does not copy a worker
tree or inspect protected aircraft data.

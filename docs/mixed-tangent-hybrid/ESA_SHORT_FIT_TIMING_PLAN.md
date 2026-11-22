# Measure whole-fit speed on a short recorded ESA prefix

Use the exact prepared input of the [closed ESA solver comparison](OBSERVED_DISPATCH_FRESH_RESULT.md).
Fix the first 120 training positions and the next 30 query times before
starting. Retain every original inertial interval needed to cover those times,
including the full latency allowance. Later receiver positions are withheld.
This is a new timing study on a shorter prefix. It leaves the 20-minute
comparison and all scientific conclusions unchanged.

Time the specified-field globe with the short error policy and zero upstream
removal, and the zero-field globe with the persistent policy and profiled
removal. Use the original first start and near-zero optimizer in both methods.
On each case, match inputs, compiler, model, active calibration columns and
forecast timestamps. Run wide precision first on one case and selective first
on the other. Record CPU and wall time for the complete calculation and for
the period from kernel availability to the saved fit. Keep compilation and
forecasting outside the fit-only time.

Keep the original relative training-cost tolerance `1e-8` and forecast
position tolerance `0.01 m`. Require both fits to converge before treating
the CPU ratio as a speed gain for an equivalent result. For this short timing
study to pass its speed gate, require a median fit CPU ratio above 1.25 and
neither pair below 1.0. Retain timing and failure evidence when a pair does
not pass. This test has no flat-disc selective solver and provides no speed
estimate for a full recorded 20-minute fit.

Freeze two pairs, two single-thread workers, at most 20 fit evaluations
and one forecast per method, and a 900-second cooperative limit. Set the
same separate 900-second limit for qualified technical recovery. Charge each
native operation before it runs. Use the shared timing wrapper and validate
the short input layout and the numerical speed gate on small controls. Read
no original recording or reserved flight and perform no forecast scoring.

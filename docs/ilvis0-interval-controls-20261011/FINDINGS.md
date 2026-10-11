# What the interval controls establish

**The calibration error in the short synthetic controls has an identifiable
numerical component.** All nine new fits converged and passed their prediction
checks. The original three coarse fits were reused without refitting; no NASA
recordings were fitted. See the [complete comparisons and figure](README.md).

With the same trajectory, calibration, receiver timestamps and solver, halving
the integration interval reduced Z gyro-offset error to 24.9–25.1% of its original
value. Quartering the interval reduced it to 6.07–6.29%. All three true models show
approximately the same square-of-interval trend, consistent with finite-interval
approximation error amplified by a weak calibration direction.

At the finest interval, adding prescribed roll while keeping the receiver path and
calibration unchanged reduced the remaining offset error by another factor of
34–42. Absolute errors were 0.00084–0.00094°/hour, compared with 0.028–0.039°/hour
without added roll. This checks geometry separately from interval size. It does not
establish how much roll, bias information or preprocessing exists in the NASA data.

The practical consequence is that a very small position residual can conceal
substantial calibration error. Solver convergence alone did not catch it; independent
known-motion controls did. This is a reason to qualify the measurement/integration
model before interpreting calibration boundaries or expanding observed fits.

The finer samples here were independently generated from known continuous rates.
Actual archival packets cannot be subdivided to recover unknown motion within them.
The next step is to test an independently derived coning/sculling treatment at the
original 200 Hz, under explicit increment conventions. See the
[next integration check](NEXT_STEP.md). Original studies and evidence remain frozen.

# Short-term variation in the saved ESA rates

This diagnostic asks how the logged rates vary over short intervals. It uses
only the earlier training portion of the already prepared first twenty-minute
development interval in recording 187. It does not open original files, later
receiver positions or protected flight groups. There are no model fits,
trajectory integrations or changes to existing error assumptions.

Preserve all three gyroscope and three accelerometer channels in their logged
engineering units. Choose the training cutoff from the frozen query layout.
Reject nonfinite values, reversed timestamps, unsupported gaps or a changed
preparation/source binding. Retain the actual timestamps; do not interpolate.

At fixed sample strides 1, 3, 30 and 300, form disjoint triples of rate samples.
Subtract the straight line between the endpoints from the middle sample,
using actual elapsed times. Divide by the Euclidean norm of these three
weights. This normalization would preserve the variance of independent,
equal-variance point errors. That error law is a hypothetical interpretation,
not a property established for the logged rates. Triples are disjoint within
each stride; results from different strides are dependent.

Report the sample counts, actual time separations, RMS and median absolute
contrasts, robust upper-tail size, means and ranges. Keep angular rates and
specific force distinct. No expected rotation field, fused attitude or fitted
aircraft motion is subtracted. Aircraft motion, vibration, filtering and noise
can all contribute. Linear motion in time cancels; other motion need not.

Do not convert logged point-rate variation into an angle/velocity random-walk
specification. In particular, the linear-point integration used for ESA creates
shared-endpoint correlations that are absent from independently perturbed
synthetic increments. A physical noise law needs a separate sampling/filtering
model. This diagnostic supplies no calibrated confidence or instrument limit.

The allowance is one saved-data identity, at most 360,100 input samples and
the resulting earlier training prefix, four fixed strides, one numerical
thread and a five-minute cooperative ceiling. Charge input samples and each
contrast before calculation. No retries, native calls, optimizer starts,
original reads or protected reads are allowed.

Qualify independent arithmetic examples, irregular timestamps, linear-trend
cancellation, signed axes, disjoint indices, malformed input, preservation of
inputs and training-only selection before execution. Bind source and runtime
versions. Audit saved outputs and hashes without repeating the numerical work.
Any uncertainty-model revision requires its own frozen qualification; neither
the active noise test nor its accuracy criteria may be changed.

[Prediction error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

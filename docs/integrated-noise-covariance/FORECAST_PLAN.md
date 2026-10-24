# Condition future errors on earlier observations only

This extends the checked linear covariance component with conditional future
means and per-epoch covariance. Use only an explicit forward checkpoint from
earlier residuals. Supply no later residuals. Keep the fixed transitions,
process loadings and receiver loadings unchanged.

The innovations at later epochs are unknown random variables. Setting their
expected value to zero gives the conditional mean. Their variance must remain
in the forecast: propagate the covariance of the random innovations-driven
mean and add each innovation covariance. Using only the saved innovation
variance would incorrectly act as if earlier withheld positions were known.

Compare every future mean and diagonal covariance block with independent dense
Gaussian conditioning at several training cutoffs, including no training and
the complete-record boundary. Retain cross-axis covariance and irregular times.
Reject changed configurations, malformed state, inverse checkpoints and
multi-column checkpoints. Demonstrate independence from unused later residuals.

Retain all 26 earlier whitening/analytic/scaling controls. The complete local
suite uses at most 64,080 generated epochs, 128 MiB of stored operator arrays,
one numerical thread and no native calls, optimizer starts, original reads,
protected reads or random draws. No aircraft error law is estimated. Preserve
the first qualification's exact eight-source snapshot and test report.

This is conditional Gaussian software with fixed parameters and a declared
mean. It does not include uncertainty from fitted calibration or noise
parameters, establish coverage for the archive, or authorize observed fitting.

[Original component plan](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

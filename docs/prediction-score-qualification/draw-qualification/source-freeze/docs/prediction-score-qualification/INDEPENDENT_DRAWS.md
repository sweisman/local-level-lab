# Independent draws without changing the noise law

The [saved fitted-prediction scores](../fitted-prediction-scores/README.md) use
one shared seed. Ten of twelve training-selected comparisons are available;
their largest coordinate error/noise ratios range from 5.29 to 6.25. These are
not significance levels or a calibrated prediction interval.

The next full-pipeline qualification needs genuinely new noise realizations.
First separate the draw seed from the covariance definition. The existing
generator recognized its two noise laws by comparing the complete settings
dictionary, including the seed. The revised generator separates that identity:
a different seed must not be mistaken
for a different covariance, a different input format, or an invalid experiment.

Keep every noise amplitude, correlation time, input format, stream label and
historical default fixed. Permit an explicitly supplied unsigned 64-bit seed.
Changing it must change the generated sensor and receiver errors while leaving
the implied noise law and the complete draw allowance unchanged. Reject changes
to other settings rather than silently accepting a new law.

Qualify both input formats against the frozen earlier generator at the original
seed. Require identical output arrays, bindings and charges. Test new-seed
repeatability, different-seed variation, earlier-prefix preservation, covariance
invariance and invalid-seed rejection before any generation. These are short
local software checks, with no fitting or archive measurements.

Only then prepare the separate full-pipeline draw study. Its finite freeze must
give each realization an immutable seed and role, preserve all intended model
and processing cases, and retain both training-selected and failed starts.
Calibration and validation seeds must be disjoint. The small first pilot must
not be presented as estimating a rare-tail quantile or calibrated coverage.

No completed study is restarted, and no existing accuracy screen or calibration
bound is changed. The reserved ESA groups remain closed.

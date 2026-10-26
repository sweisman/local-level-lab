# Separate calibration and validation targets

The first ledger qualifies 26 checks and remains preserved in its frozen
snapshot. Before using the higher-power campaign example, support its distinct
targets explicitly: calibration seeks a 99% tolerance limit; independent
validation tests a 95% coverage requirement. The original ledger derives both
from the calibration target.

Extend `lll.prediction_calibration.validate` with optional `coverage`. Omission
preserves the original target. An explicit value is a frozen validation-policy
input, never selected from validation outcomes. Record both targets in the
result and leave the calibration artifact unchanged. The common population
and draw-role checks still apply.

Qualification has a separate finite allowance: four new deterministic checks
plus the 26 existing regressions, one numerical thread, two reserved threads,
two minutes per test group, zero draws, fits and native calls. Use 299 fixed
calibration scores at 99% content and 181 validation scores with four strict
exceedances. The 95% one-sided binomial upper bound must pass a 5% failure
target and fail the original 1% target. Reject invalid explicit probabilities.

Bind the revised sources and environment before the formal test report.
Preserve the first ledger's source snapshot and results. No campaign starts,
aircraft fitting or protected ESA observations are authorized by these checks.

[Campaign sizing](CAMPAIGN_SIZING.md) · [Original ledger plan](CALIBRATION_PLAN.md).

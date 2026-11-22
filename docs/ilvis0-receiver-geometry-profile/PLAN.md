# Conditional model-contrast geometry in longer tracks

## Question

For the 29 sealed receiver/raw candidate intervals, how much of each
Earth-model angular-rate contrast remains after the existing local nuisance
projection, **if aircraft angular motion were independently known**? This is
a geometry diagnostic, not an observed gyro result or eligibility gate.

## Fixed method

Reproduce each candidate interval and source SHA-256 from the sealed
[receiver/raw inventory](../ilvis0-receiver-raw-inventory/RESULT.md). Use its
dated primary-receiver positions, never Group-1 attitude or gyro residuals.
Take 30-second local slopes of reported latitude and longitude at original
receiver times, without filling gaps. Use the same three specified physical
rate patterns and `contrast_envelope` in the existing observation library.
Evaluate all three model pairs across its fixed ±15° crab and ±5° roll/pitch
envelope, all physical anchors and all three declared nuisance treatments.
Save the worst retained fraction and residual vector RMS for each pair and
treatment. No threshold or model decision is applied.

The coordinate rates are conditional on the receiver's geodetic chart. The
calculation assumes aircraft rotation can be removed independently, uses
uniform diagnostic weights, and does not establish calibrated power, global
nonlinear identifiability or level flight. Unrestricted aircraft rotation
can absorb these angular-rate contrasts. The recorded IMU observations are
not scored in this study.

Freeze the exact 29 source hashes and segment IDs, code, inputs, numerical
environment, one worker and thread, a two-hour cooperative limit and zero
Earth-model fits. Qualify task-level recovery first. Publish every result,
including failures, without changing the original 53-stretch study or the
reserved ESA groups.

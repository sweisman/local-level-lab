# Known-calibration substitution control

## Fixed question

In the two previously closed bound-aware generated cases, does replacing
fitted sensor settings with the **known generating values** materially change
the native path miss? This is an attribution diagnostic, not a new fit or an
estimator that can be used on aircraft.

Reconstruct the exact original noisy IMU and training receiver arrays from
their frozen seeds, and verify all saved input hashes and the unchanged native
baseline path before scoring. For each case, compute exactly four forecasts:

1. Saved fitted parameter vector (baseline).
2. Replace only the twelve gyro/accelerometer bias and gain coordinates with
   their known generating values; keep all other fitted coordinates.
3. Replace only gravity adjustment and time offset with their known generating
   values; keep all others fitted.
4. Replace all fourteen named coordinates together.

The physical normalized coordinate equals its generating value divided by
the original declared half-range. All substitutions must remain inside the
unchanged box. Preserve the fitted initial state, mount and lever corrections,
trajectory, clock convention and every measured/generated IMU increment.
Score training and later horizontal/vertical position error against the same
sealed known truth. Do not refit any remaining nuisance parameter.

Require source-bound software checks, reboot recovery qualification and a
passing short preflight before the full two-case study. Reserve four native
forecasts per case, including baseline, with finite packet-visit charges; use
at most two one-thread workers. Keep all failures. No recorded or reserved
aircraft input is read. A better path after substitution would show
sensitivity to that parameter block in these synthetic cases, not identify
the actual cause or calibrate uncertainty. Scientific decision: **abstain**.

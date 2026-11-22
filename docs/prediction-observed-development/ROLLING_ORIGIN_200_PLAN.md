# Earlier-origin error development check

## Question

Does the existing specified-field globe calculation transfer across a
different part of the **same opened ESA flight**? Fit on receiver reports
0–199, then predict reports 200–319. This tests how much the favorable 400/120
forecast depends on its start time. It cannot calibrate coverage or confirm an
Earth model because the two windows share a flight and instrument.

## Fixed design before fitting

- Reuse the verified prepared recording-187 inputs. No original download or
  reserved confirmation group is opened.
- The fit receives only the first 200 receiver positions. It receives IMU
  increments through report 319 and the 320 report times. The 120 scoring
  positions remain outside the fit worker until both laws have sealed.
- Fit the specified-field globe with the unchanged header-elapsed clock,
  physical bounds, single start and 200-evaluation stopping rule. Run both
  existing `increment` and `point` error laws; do not select one using its
  future error.
- Allow two workers at one numerical thread each, with at most 700,000 native
  calls and 45,000,000,000 packet visits per fit. The original study wall
  ceiling is two hours. An interrupted unfinished task needs separately
  frozen recovery with unchanged scientific inputs and charged starts.
- Require source/environment qualification, a generated split test, a
  reboot/interruption recovery test and hash-bound inputs before launch.
- Only after both fit tasks close, score signed north/east/up errors,
  horizontal/height RMS, numerical convergence, active bounds and nominal
  interval coverage. Report every failure. The decision remains **abstain**.

The [saved-input preflight](ROLLING_ORIGIN_200_PREFLIGHT.md) establishes the
200/120 boundary. The prior [400/120 check](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md)
is retained unchanged. A matched earlier-origin comparison can guide the
next error-envelope design, but neither window establishes performance on a
different aircraft flight.

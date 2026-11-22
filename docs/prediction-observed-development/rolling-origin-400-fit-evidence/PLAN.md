# Earlier-origin prediction diagnostic

## Question

Does the specified-field globe fit trained on the first 400 receiver reports
of the already opened ESA development recording predict reports 400–519 with
physically adequate position errors? This is a development diagnostic of
forecast growth. It is not an independent flight, an Earth-model decision or
a calibrated uncertainty test.

The 120-report horizon was chosen after earlier forecasts from this recording
were examined. Results cannot independently validate that horizon. Preserve
the completed 600/200 and 800/400 results unchanged, including their failures.

## Design to freeze before fitting

- Source: hash-verified prepared interval for ESA recording 187; no original
  download and no reserved confirmation flight group.
- Training: receiver reports 0–399. The worker receives inertial increments
  through the prediction horizon, but cannot read later receiver positions.
- Prediction: the next 120 receiver times, through report 519, with packet
  support for the declared timing-offset bound. Retain reports 400–519 in a
  separate scoring artifact until both forecasts seal.
- Physical candidate: specified-field globe only. This is a forecast-error
  diagnosis, not a shape comparison.
- Error assumptions: both existing increment and point-rate laws, with their
  unchanged noise parameters. Score both; do not choose by future outcome.
- Clock, calibration bounds, start, optimizer and stopping rule: copy the
  sealed parent recipe exactly. It permits 200 evaluations; use one fixed
  start per law. Do not increase an allowance or retry a completed failure.
- Each of the two tasks has a maximum of 700,000 native calls and
  45,000,000,000 packet visits, charged before execution. Reserve two workers
  at one numerical thread each and a four-hour original wall allowance.
  An unfinished task may continue only under a separately frozen recovery
  allowance of at most two attempts and two technical interruptions, with
  unchanged inputs and no restart of sealed outcomes.
- Require source/environment qualification, hash-bound input staging and a
  verified reboot/interruption recovery test before launch.
- Score saved forecasts against the separately held reports only after both
  fit tasks close. Report signed north/east/up errors, horizontal and height
  RMS, complete-stretch physical adequacy, fitted-bound activity, numerical
  stopping and nominal interval coverage. Failure and abstention remain
  visible. No scientific decision follows.

The test uses one earlier origin on one development flight. It may expose
when the height error begins, but it cannot identify whether the cause is
sensor error, aircraft motion, calibration, receiver error or timing. The
seven reserved ESA groups stay closed until a separately qualified method,
error range and decision policy are frozen.

The [saved-input preflight](ROLLING_ORIGIN_400_PREFLIGHT.md) verifies 400
training reports, 120 withheld reports and 155,868 IMU packets through the
prediction end. The new study identity is
`esa-rolling-origin-400-development-v1-20261115`. Source-bound tests and a
separately frozen recovery policy must pass before that study starts.

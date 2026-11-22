# Fixed-error-law paired motion pilot

## Question

Does the existing 15-state prediction-error law behave differently when a
known 0.37 Hz aircraft motion changes the receiver's one-second positions?
This is a software-control pilot, not an aircraft prediction or a repeat of
the failed 256-history coverage validation.

## Predeclared cases

Use exactly 16 untouched seeds `2026112300`–`2026112315`. For each seed,
generate one motion-off and one motion-on 120-second history at 100 Hz,
using identical gyro, accelerometer and receiver error draws. Use the
unchanged 15-state law and fixed scales from the earlier generated check.
Condition only on receiver reports 0–60, save both forecasts, then score
reports 61–120. Preserve every technical failure. Report paired maximum
standardized-error differences, whole-history range misses and discordant
pairs. No coverage-certification threshold is assigned to 16 cases.

Use one worker and one numerical thread, one original start per seed pair,
at most 24,000 generated IMU packets and 242 receiver reports per pair,
and a 15-minute original wall allowance. Freeze source, inputs, environment
and finite recovery before launch. The continuation is separately charged
and cannot change the scientific method. No aircraft original, protected
ESA group or Earth-model fit is allowed.

# Preparing the matched inertial comparison

Use the two southern recordings already chosen for the GPS reconstruction.
The [saved layout](matched-observed-layout.json) binds their original source
hashes and flight groups to the same recorded times. It confirms 668 exact
common epochs for IMU8 and 443 for IMU21. The first 445 and 295 epochs form
the respective training sets. The 223 and 148 remaining epochs are scored
after forecasting.

For the input preflight, extract the original signed increments with the
existing installation, status and unit checks. Preserve the original
packet identifiers and the measured header intervals. Verify that every
receiver epoch has valid packet support under both the nominal sample
period and elapsed-header clock. Bind onboard, L1 and dual-frequency
coordinates to the same epochs by the saved GPS-to-UTC offset. Keep the
later positions physically separate from the input to fitting. This
preflight uses two retained originals and zero model fits.

The subsequent numerical preflight should exercise all four shape and
field combinations on the prepared input. It must use matching starts,
calibration bounds and evaluation allowances, and verify that training
ends before scoring positions are loaded. Preserve failed stops and
prediction inadequacy as different outcomes. Freeze the full offset and
processing comparison separately after checking that the real input works.

These recordings are development material. Compare forecasts against the
three GPS streams to measure processing sensitivity. A future calibrated
decision still requires independently supported common receiver error and
validation by flight group.

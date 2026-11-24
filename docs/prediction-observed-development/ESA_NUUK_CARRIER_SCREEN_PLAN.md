# Explain the missing seconds in the nearby Nuuk comparison

Use the same permanent Nuuk excerpt, saved aircraft satellite support,
and original two-minute time window as the nearby-station comparison.
Record which ground observations are rejected for unavailable fields,
carrier lock, the L1 Doppler check or the two-band phase check. Replay
the same station screen without its range geometry calculation and check
that the result agrees with the diagnostic classifications. Check the
saved retained rows against the resulting satellite sets.

For each interval with at least five numeric Doppler differences, report
their median and their dispersion about that median. This checks whether
several satellites share a common offset. It changes no input, threshold,
score or previously saved outcome.

One local task with one worker and one thread may read the sealed inputs
once and apply 120 diagnostic checks, plus one setup check, with a
30-second cooperative cap. No new fits, downloads or reserved data.

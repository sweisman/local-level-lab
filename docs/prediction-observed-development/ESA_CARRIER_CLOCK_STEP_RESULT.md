# The recorded GPS clock change explains the carrier break

All 12 GPS satellites at the exceptional half-second pair pass both
original continuity limits after accounting for a one-millisecond
receiver clock step. The recorded clock offset changed by **0.998784 ms**,
giving an elapsed GPS interval of **0.4990012 s**.

After subtracting the common clock step from each carrier phase,
the largest L1 disagreement with Doppler was **0.077 cycles**.
The largest difference between the two phase-derived range changes
was **6.7 mm**. Both fall within the method's original screens.
The calculation used the two original phase values on each band.
It performed no position fit and supplied no missing sample.

The original raw-data rejection stays in the continuity record.
The adjustment defines a separate processing check on that one pair.
It does not qualify clock corrections elsewhere in the archive.

[Method and thresholds](ESA_CARRIER_CLOCK_STEP_PLAN.md) ·
[Frozen inputs](esa-carrier-clock-step-freeze.json) ·
[Per-satellite results](esa-carrier-clock-step-result.json)

# Compare the aircraft and fixed receiver at the Reykjavík stop

Use the [61 fixed receiver epochs](ESA_FIXED_REFERENCE_WINDOW_RESULT.md)
and the existing speed-selected stop in opened ESA recording 187.
Use only the original `air10706a.23o` observations for the aircraft.
Freeze both station identities, the file size, source receipts and exact
GPS week and second targets before reading the aircraft window. Bounded
reads must confirm the same logged aircraft source and retain exact
epoch records, without downloading a new recording or opening a reserved
flight. A day or time-scale mismatch ends the acquisition attempt.

Reuse the sealed source listing and 256 KiB prefix. Allow up to 16
time-location probes of 256 KiB and 28 successive 1 MiB reads with
128-byte overlaps. Charge up to three transport attempts per exact
byte range, capped at 96 MiB requested bytes in total. A resume uses
only the same hashed inputs and existing attempt ledger. Scan between
fixed-station epochs so an aircraft loss-of-lock indicator or missing
half-second sample can break a proposed arc.

At each matched GPS time, require normal epoch flags and count common
satellites with the same recorded GPS code and carrier signals. Keep
missing epochs, loss-of-lock indicators and firmware/time metadata.
Compare only uninterrupted arcs. Freeze a deterministic reference
satellite rule from availability and elevation before comparing
residuals. The first output is a coverage and signal table. Freeze a
separate finite calculation before fitting any differential paths.

The fixed station is less than 1 km from the aircraft at this stop.
Common-satellite differences can help check shared satellite and nearby
propagation errors. This ground check cannot measure Greenland airborne
errors or establish independent-flight prediction coverage. No aircraft
IMU fitting or Earth-model scoring enters the source qualification.

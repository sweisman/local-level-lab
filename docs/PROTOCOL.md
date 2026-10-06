# Participant protocol

The in-app instructions are in `android/app/src/main/java/io/github/sweisman/locallevellab/ui/Instructions.kt`. Keep their guidance consistent with this checklist. A completed recording does not by itself establish scientific eligibility.

1. **Before you fly.** Charge the IMU and the phone. Pair the IMU, choose it in Settings, and tap **Write and verify IMU settings**. Allow recording with the screen off. Set the phone's date and time automatically before going offline; the recorded phone-clock anchors help later alignment but do not certify UTC accuracy. Bring a rigid mount (see the README for examples). Book a window seat if you can. Create a session using the required flight details below.
2. **Pre-flight calibration (~25 min).** Put the IMU on a solid table, one long side against a straight edge. Visit 4 positions, then go back through them in mirror order: label up, label up turned 180°, label down, label down turned 180° (one double-length stay), label down, label up turned 180°, label up. That is 7 placements, about 3 still minutes each. Don't touch anything.
3. **Optional drift run.** 30+ minutes lying still, for example overnight.
4. **Mount the IMU.** Best is a window frame or sidewall mount. Good is clamped to the seat structure. Acceptable is fixed to a locked tray (cruise only). Never hold it or leave it loose, and don't connect a cable. The orientation doesn't matter as long as it stays fixed. Optionally choose window/middle/aisle; no exact seat number is collected. Run the placement check (60 s stable). The phone can be anywhere it gets GPS.
5. **Record the flight.** Airplane mode on, then Bluetooth and Location on. If there is no fresh GPS fix, acknowledge **Record without a fresh GPS fix** on the placement screen and keep recording. Precise-location permission, the 60-second placement check and verified IMU settings are still required. Record as much of the cruise as you can, including a natural banked course change to help find the aircraft's nose direction. The screen can be off. If turn reminders are on, turn the IMU slowly, over about five seconds, to face the opposite way, keeping the same side up, fix it firmly again and confirm. Turning it upside down helps much less; if your mount allows only that, choose it in Settings. Tap **I moved the IMU** if it gets bumped.
6. **Post-flight calibration.** The same 7 placements, as soon as you can after landing.
7. **Upload or share.** Uploads happen only after you tap Upload and explicitly consent to permanently publishing the original recording and identifying metadata. Flight recording requires precise-location permission; missing or stale GNSS requires explicit acknowledgment.

## Required flight details

| Field | What to enter |
|---|---|
| Operating airline | Select the airline operating the aircraft from the searchable directory. Search by name, IATA/ICAO code or country; check the full name when codes are shared. |
| Operating flight number | Enter the number alone or with that carrier's prefix: for example, `10`, `EY10` or `ETD10` for Etihad. For a codeshare, use the operating flight rather than a different marketing carrier's number. |
| Departure date | The **scheduled departure date at the origin**, in `YYYY-MM-DD` format. Confirm the default, which comes from the phone. Keep the scheduled date if a delay crosses midnight. |
| From / To | Different three-letter IATA airport codes, for example `ORD` and `AUH`. |

Aircraft type, notes and seat position are optional; no exact seat number is collected. The directory
includes historical carriers and is not a current operating-status register. A missing carrier needs
a directory update; do not select another carrier to get past setup.

**Open flight history** opens FlightAware in your external browser. Check the actual date and route
when connectivity is available. A future flight may have no track yet. The app checks entry format
and carrier-prefix consistency, not airport existence or whether a flight operated. Opening the
link leaves verification pending and contacts a website separately from session-upload consent.

## Missing GPS and public-track checks

Missing GPS does not stop IMU capture after acknowledgment. The phone continues looking for GPS
and records fixes if reception returns. Check the IMU link and activity log separately from GPS
reception. Continue the normal mount-turn and post-flight calibration steps.

After landing, promptly save a complete public track if GPS was missing or to cross-check collected
GPS. Preserve the exact historical link, provider, flight date/route, downloaded position/time table,
displayed timezone, reporting-source labels, estimate labels and gaps. A map screenshot alone is
insufficient. Do not assume displayed times are UTC: departure-local date and the first UTC
observation may fall on different days. A complete table may still contain estimated positions and gaps.

Keep the original session unchanged and share the external track as a separate artifact. Provider
terms remain applicable; the recording's CC0 release does not relicense third-party tracks.

An observed track can potentially cross-check phone GPS or recover missing trajectory geometry.
The present analysis does **not** automatically substitute it for phone GNSS. Scientific use requires
verified identity, recording-time overlap, adequate observed coverage, checked clock alignment and
a validated timing/position uncertainty model. Coarse samples may miss turns. Estimated positions
and long gaps cannot be treated as measured fixes; a position track alone supplies no IMU evidence.
See [VALIDATION.md](VALIDATION.md#external-flight-tracks-and-missing-gnss) for the analysis boundary.

**Controls:**

- Turn the IMU to face the opposite way, same side up, during long flights.
- Mount two IMUs in different orientations.
- Ground-only stationary recordings (Settings → bench capture) test Earth rotation at your latitude.

Always follow crew instructions and airline rules on devices.

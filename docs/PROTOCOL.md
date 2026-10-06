# Participant protocol

The same text appears in the app (Instructions). The source of truth is `android/app/src/main/java/io/github/sweisman/locallevellab/ui/Instructions.kt`. Keep the two in sync.

1. **Before you fly.** Charge the IMU and the phone. Pair the IMU, choose it in Settings, and tap "Write and verify IMU settings". Allow recording with the screen off. Bring a rigid mount (see the README for examples). Book a window seat if you can. Create a session with the operating airline from the searchable directory, its flight number, the departure date at the origin, and origin/destination IATA codes. Use the operating flight for codeshares. Open flight history to check the date and route; valid entry alone does not verify that a flight flew.
2. **Pre-flight calibration (~25 min).** Put the IMU on a solid table, one long side against a straight edge. Visit 4 positions, then go back through them in mirror order: label up, label up turned 180°, label down, label down turned 180° (one double-length stay), label down, label up turned 180°, label up. That is 7 placements, about 3 still minutes each. Don't touch anything.
3. **Optional drift run.** 30+ minutes lying still, for example overnight.
4. **Mount the IMU.** Best is a window frame or sidewall mount. Good is clamped to the seat structure. Acceptable is fixed to a locked tray (cruise only). Never hold it or leave it loose, and don't connect a cable. The orientation doesn't matter as long as it stays fixed. Optionally choose window/middle/aisle; no exact seat number is collected. Run the placement check (60 s stable). The phone can be anywhere it gets GPS.
5. **Record the flight.** Airplane mode on, then Bluetooth and Location on. Record as much of the cruise as you can, and keep recording through at least one course change of the aircraft (the analysis needs one banked turn to find the nose direction). The screen can be off. If turn reminders are on, turn the IMU slowly, over about 5 seconds, to face the opposite way, keeping the same side up, and confirm. That is what makes a straight route count. Turning it upside down helps much less; if your mount allows only that, choose it in Settings. Tap "I moved the IMU" if it gets bumped.
6. **Post-flight calibration.** The same 7 placements, as soon as you can after landing.
7. **Upload or share.** Uploads happen only after you tap Upload and explicitly consent to permanently publishing the original recording and identifying metadata. Flight recording requires precise-location permission; missing or stale GNSS requires explicit acknowledgment.

**Missing GPS and public-track checks.** Acknowledge a missing fix on the placement screen and keep recording the IMU; the phone continues looking for GPS. After landing, promptly save the complete public track, source link and displayed timezone. Observed positions with usable timestamps and coverage may recover trajectory geometry, and can cross-check collected GPS. Preserve provider estimates and long gaps explicitly. Keep the original recording intact: scientific use of an external track still requires checked time alignment and an uncertainty model. The app's flight details and phone-clock anchors support that work; no automatic fallback is currently used by the analysis.

**Controls:**

- Turn the IMU to face the opposite way, same side up, during long flights.
- Mount two IMUs in different orientations.
- Ground-only stationary recordings (Settings → bench capture) test Earth rotation at your latitude.

Always follow crew instructions and airline rules on devices.

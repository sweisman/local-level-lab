# Participant protocol

The same text appears in the app (Instructions). The source of truth is `android/app/src/main/java/io/github/sweisman/locallevellab/ui/Instructions.kt`. Keep the two in sync.

1. **Before you fly.** Charge the IMU and the phone. Pair the IMU, choose it in Settings, and tap "Write and verify IMU settings". Allow recording with the screen off. Bring a rigid mount (see the README for examples). Book a window seat if you can.
2. **Pre-flight calibration (~25 min).** Put the IMU on a solid table, one long side against a straight edge. Visit 4 positions, then go back through them in mirror order: label up, label up turned 180°, label down, label down turned 180° (one double-length stay), label down, label up turned 180°, label up. That is 7 placements, about 3 still minutes each. Don't touch anything.
3. **Optional drift run.** 30+ minutes lying still, for example overnight.
4. **Mount the IMU.** Best is a window frame or sidewall mount. Good is clamped to the seat structure. Acceptable is fixed to a locked tray (cruise only). Never hold it or leave it loose, and don't connect a cable. The orientation doesn't matter as long as it stays fixed. Enter your seat (for example 23A). Run the placement check (60 s stable). The phone can be anywhere it gets GPS.
5. **Record the flight.** Airplane mode on, then Bluetooth and Location on. Record as much of the cruise as you can, and keep recording through at least one course change of the aircraft (the analysis needs one banked turn to find the nose direction). The screen can be off. If turn reminders are on, turn the IMU slowly, over about 5 seconds, to face the opposite way, keeping the same side up, and confirm. That is what makes a straight route count. Turning it upside down helps much less; if your mount allows only that, choose it in Settings. Tap "I moved the IMU" if it gets bumped.
6. **Post-flight calibration.** The same 7 placements, as soon as you can after landing.
7. **Upload or share.** Uploads happen only when you tap Upload.

**Controls:**

- Turn the IMU to face the opposite way, same side up, during long flights.
- Mount two IMUs in different orientations.
- Ground-only stationary recordings (Settings → bench capture) test Earth rotation at your latitude.

Always follow crew instructions and airline rules on devices.

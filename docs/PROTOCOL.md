# Recording a flight

An **IMU (inertial measurement unit)** is the external device that measures turning and acceleration.
The phone records the IMU and supplies GPS positions.

This guide explains how to collect a complete, reviewable recording. It does not promise that
the flight will distinguish the Earth models. That depends on the instrument, route, data
quality and analysis. Read [How the experiment works](METHODOLOGY.md) and arrange the
[instrument checks](BENCH.md) before planning to use a flight as scientific evidence.

## Before leaving

Charge the phone and IMU. Pair them, select the instrument in Settings, and tap
**Write and verify IMU settings**. Check that recording
can continue with the screen off. Set the phone date and time automatically before going
offline; the recorded clock information helps later checks but does not certify exact UTC time.

Create a session with the operating airline, operating flight number, scheduled departure date
at the origin, and departure and arrival airport codes. For a codeshare, use the airline actually
flying the aircraft. Keep the scheduled origin date if a delay crosses midnight.

The searchable airline directory includes historical entries. Selecting a carrier and entering
a valid number does not verify that a flight operated. **Open flight history** opens an external
website where the date and route can be checked; opening it does not complete verification.

## Calibrate before the flight

Allow about 25 minutes on a solid, stationary table. Follow the seven placements shown by the
app. They visit four positions and return through them in reverse order. Keep each placement
still for about three minutes; the middle placement lasts twice as long. A straight edge helps
you return to the same facing direction. Do not touch the IMU during a still recording.

An optional still recording of 30 minutes or more can help characterize drift. It does not
replace the full calibration or bench tests.

## Mount and record

Fix the IMU firmly to a suitable surface, following airline and crew instructions. A locked
tray is usable only during cruise. Do not hold the IMU or leave it loose. It must be possible
to turn it deliberately and secure it again. The phone can be elsewhere if it receives GPS.

Complete the 60-second placement check. Use airplane mode with Bluetooth and Location enabled
where permitted. Record as much cruise as possible, including natural course changes; these
help the analysis determine the aircraft direction relative to the IMU. Recording can
continue with the screen off.

When following a turn reminder, wait for steady cruise. Slowly turn the IMU to face the
opposite way, keeping the same side up, over about five seconds. Secure it again and confirm
the turn in the app. Choose a steady period before, during and after the movement; avoid doing
this while the aircraft banks or turns. Aircraft motion during the movement can be mistaken
for a change in IMU orientation. Turning upside down
provides different, often less useful information; choose that option in Settings if it is the
only movement the mount permits. Tap **I moved the IMU** if it is bumped unexpectedly.

## If GPS is unavailable

Acknowledge **Record without a fresh GPS fix** and keep the motion recording going. Precise
location permission, verified instrument settings and the placement check are still required.
The phone will continue looking for fixes and save them if reception returns.

After landing, save the complete public flight track if possible. Keep its provider, exact
history link, date, route, displayed timezone, position-and-time table, estimate labels and gaps.
A map screenshot alone is insufficient. Do not assume the displayed times are UTC.

Keep that track separately from the unchanged original recording. A position export can help
cross-check GPS and may eventually recover the route; it contains no IMU data.
Replacing missing phone GPS with an external track is not yet a validated part of the analysis.
Provider terms still apply to the downloaded track. See [Validation](VALIDATION.md#external-flight-tracks-and-missing-gnss).

## After landing

Repeat the same seven-placement calibration as soon as practical. Keep the complete session,
including both calibrations, recording interruptions and unexpected movements. Do not edit
the raw recording to improve its appearance.

You can share a session privately or upload it. Uploading requires explicit consent to
permanently publish the original recording and identifying flight details. Read the
[privacy policy](../PRIVACY.md) before consenting. Saving or uploading a recording does not
by itself make it eligible for the main research result.

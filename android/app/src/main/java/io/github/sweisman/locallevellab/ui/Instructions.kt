// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

/** In-app protocol. It matches docs/PROTOCOL.md; keep the two in sync. */
data class Section(val key: String, val title: String, val body: List<String>)

val INSTRUCTIONS = listOf(
    Section("about", "What this measures", listOf(
        "A gyroscope measures angular velocity relative to inertial space (a non-rotating reference frame), not relative to the ground.",
        "If the Earth turns, a sensor resting on it turns with it. A rotating globe gives about 15°/hour, split between the vertical and horizontal depending on latitude. A still Earth gives zero. A spinning flat disc would give 15°/hour about the vertical everywhere, but that can't be told apart from the sensor's own offset, so the flat model tested is the still disc.",
        "As an aircraft moves, its local horizontal (\"local level\") turns relative to inertial space. On a globe it tilts forward at about 8°/hour at 900 km/h and turns slowly about the vertical. On a flat disc it never tilts, but an eastbound flight circles the centre and turns about the vertical.",
        "A small motion sensor (the IMU) records the raw rotation. Your phone records GPS and shows a dashboard. The analysis compares the data against three models: a rotating globe, a still globe and a still flat disc. The predictions come from GPS alone and never from the gyro.",
        "These signals are tiny next to the sensor's own drift, so careful calibration and a rigid mount matter more than anything else. Many flights pooled together give the final answer.",
    )),
    Section("before", "Before you fly", listOf(
        "Charge the IMU and the phone fully. A power bank for the phone is fine; the IMU runs on its own battery.",
        "Pair the IMU and choose it in Settings, then tap “Write and verify IMU settings”.",
        "In Settings, allow recording with the screen off, so the phone can't stop the recording to save battery.",
        "Set the phone's date and time automatically before going offline. Recorded phone-clock anchors help align a public track later, but they do not certify UTC accuracy.",
        "Bring a rigid mount: a clamp or suction window mount, or Dual Lock / Velcro. Examples are listed in the README.",
        "Book a window seat if you can. GPS needs a view of the sky, and the sidewall is the stiffest place to mount.",
        "When creating a flight session, choose the operating airline from the searchable directory and enter its flight number, the departure date at the origin, and the origin/destination airport codes. On a codeshare, use the operating flight. Open flight history to check the date and route; entering valid details alone does not verify a flown flight.",
        "Use the scheduled departure date at the origin, even if a delay crosses midnight. Confirm the default date, which comes from the phone. The directory includes historical carriers; a missing carrier needs a directory update. Flight setup checks entry format, not airport existence or whether the flight operated.",
        "Do the pre-flight calibration at home or at the gate, on a solid table. That takes about 20 minutes.",
    )),
    Section("calibration", "Calibration (4 positions, 7 placements)", listOf(
        "Calibration measures the gyro's own offset (bias). Without it the flight data can't be interpreted.",
        "Put the IMU on a solid, level table and leave it alone. Don't touch the table, and nobody should walk heavily nearby.",
        "Position 1: label up, one long side pressed against a straight edge (a heavy book or the table edge).",
        "Position 2: label up, turned 180°, with the same long side against the same straight edge.",
        "Position 3: label down, side against the straight edge.",
        "Position 4: label down, turned 180°.",
        "Then go back through them in mirror order: position 4 continues as one double-length stay, then 3, 2 and 1 again. Seven placements in all, about 3 still minutes each.",
        "Visiting each position twice in mirror order lets the analysis measure any slow drift of the sensor during calibration and remove it.",
        "Only the seconds when the IMU is truly still count. If the counter pauses, something is shaking.",
        "Turning exactly 180° matters. It makes the Earth's rotation cancel out of the bias. Calibration also measures the horizontal part of that rotation directly, from the 180° pairs, which is a ground-level test in its own right.",
        "Repeat after landing. Comparing before with after shows how much the bias drifted during the flight.",
    )),
    Section("drift", "Drift runs (optional, valuable)", listOf(
        "A drift run is 30+ minutes of the IMU lying completely still. It shows how stable the gyro's bias is over time and against temperature.",
        "Do one before and/or after the flight, for example overnight at the hotel, label up on a solid surface. The phone's screen can be off.",
    )),
    Section("placement", "Mounting the IMU in the aircraft", listOf(
        "Best: fixed to the window frame or cabin sidewall with a clamp, suction mount or Dual Lock. The sidewall is the stiffest part of the cabin you can reach.",
        "Good: firmly clamped to the seat structure, but only where it can't come loose or get in anyone's way.",
        "Acceptable: fixed to the tray table with the tray locked. Trays flex, and they must be stowed for takeoff and landing, so start the recording once you're at cruise.",
        "Never hold it or leave it loose. Any slow turning in the mount looks like signal.",
        "Don't connect a cable to the IMU during a recording. A cable can pull it, and charging warms it.",
        "The IMU doesn't need to be level. It just has to keep the same orientation relative to the aircraft.",
        "Once it's mounted, run the placement check. The app waits until the IMU has been stable for 60 seconds.",
        "You may choose window, middle or aisle when creating a session. Exact seat numbers are not needed or collected.",
        "The phone can go anywhere it gets GPS: in a pocket by the window, or on the tray. It doesn't need to be still.",
        "Follow crew instructions and airline rules on devices at all times.",
    )),
    Section("flight", "During the flight", listOf(
        "Put the phone in airplane mode, then turn Bluetooth and Location back on. GPS works in airplane mode on most phones.",
        "Record as much of the cruise as you can, and keep recording through at least one course change of the aircraft (for example the turn onto the cruise track). The analysis needs one banked turn to find which way the aircraft's nose points relative to the IMU. Routes with north-south travel are the most informative.",
        "The phone's screen can be off. Recording carries on in the background, and the app reconnects to the IMU on its own if the link drops.",
        "If GPS is unavailable, acknowledge this on the placement screen and keep recording the IMU. The phone keeps looking for GPS. A public track may help recover the trajectory after landing; it must have observed positions, usable timestamps and enough coverage. Estimated positions and long gaps cannot substitute for measured GPS.",
        "Precise-location permission, the 60-second placement check and verified IMU settings are still required without GPS. Check the IMU link separately from GPS reception; a completed recording is not automatically eligible for scientific analysis.",
        "If turn reminders are on, the phone will buzz every so often. Slowly, over about 5 seconds, turn the IMU to face the opposite way, keeping the same side up, fix it firmly again, and tap the button on the notification or the dashboard. On a clamp mount, take it out and put it back facing the other way.",
        "Those turns are what make a straight route count: the signal moves to other sensor axes while the sensor's bias stays put. Turning it upside down helps much less. If your mount only allows that, choose it in Settings.",
        "The dashboard shows the link, both batteries, the IMU temperature, GPS, what each model predicts, and a running activity log. The live 'measured' number is only a rough 5-minute average.",
    )),
    Section("after", "After landing", listOf(
        "Do the post-flight calibration (the same 7 placements) as soon as you can, ideally within a few hours.",
        "Then tap Upload. Uploads only happen when you ask, and by default only on Wi-Fi.",
        "You can also Share the session file and analyze it yourself. The analysis software is open source.",
        "If GPS was missing, save the complete public flight track promptly, including its source link and displayed timezone. Keep the original recording intact. External tracks can also cross-check phone GPS; scientific use needs a separately checked time alignment and uncertainty model.",
        "Save the position/time table, reporting sources, estimate labels and gaps. Do not assume displayed times are UTC; coarse samples may miss turns. Share the track separately from the session zip. Automatic external-track fallback is not yet supported by the analysis, and a position track alone supplies no IMU evidence.",
    )),
    Section("controls", "Control experiments", listOf(
        "Turn the IMU to face the opposite way, same side up, during long flights (the turn reminders do this). A real rotation of the aircraft frame shows up on different sensor axes, while sensor bias stays on the same axes.",
        "Two IMUs mounted in different orientations on the same flight are an even stronger check.",
        "Stationary recordings on the ground are just as valuable. They test Earth rotation at your latitude. Settings has a bench capture for this.",
    )),
    Section("privacy", "Privacy and open source", listOf(
        "Recorded: the IMU's raw data stream, GPS during the flight only, the flight details and optional seat position you enter, and the phone model.",
        "Not recorded: your name, account, contacts or precise home location. Calibrations save only latitude rounded to 0.5°, and you can turn that off in Settings.",
        "The IMU's Bluetooth address never leaves the phone. A random unit ID links sessions made with the same IMU so its bias can be modelled, and a random install ID links your own sessions. Neither is tied to you.",
        "Uploaded data is released into the public domain (CC0) so anyone can reanalyze it. The app, server and analysis code are AGPL-3.0 open source.",
        "Airline selection is offline. Open flight history launches an external browser with the carrier and flight identifier; that website has its own privacy policy. Third-party tracks and the bundled airline directory retain their own licenses.",
    )),
)

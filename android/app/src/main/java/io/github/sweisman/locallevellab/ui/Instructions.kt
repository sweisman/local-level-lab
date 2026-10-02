// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

/** In-app protocol. It matches docs/PROTOCOL.md; keep the two in sync. */
data class Section(val key: String, val title: String, val body: List<String>)

val INSTRUCTIONS = listOf(
    Section("about", "What this measures", listOf(
        "A gyroscope measures angular velocity relative to inertial space (a non-rotating reference frame), not relative to the ground.",
        "If the Earth turns, a phone resting on it turns with it. A rotating globe gives about 15°/hour, split between the vertical and horizontal depending on latitude. A rotating flat disc gives 15°/hour about the vertical everywhere. A still Earth gives zero.",
        "If the Earth is curved, the local horizontal (\"local level\") of a moving aircraft rotates relative to inertial space, at a rate set by its speed and the Earth's radius: about 8.1°/hour at 900 km/h. On a flat Earth it's zero.",
        "Your phone records raw sensor data. The analysis compares it against all four combinations (flat or sphere, still or rotating) and reports which one fits. The predictions come from GPS alone and never from the gyro.",
        "These signals are tiny next to a phone gyro's own drift, so careful calibration and a phone that stays perfectly still matter more than anything else. Many flights pooled together give the final answer.",
    )),
    Section("before", "Before you fly", listOf(
        "Charge the phone fully. A recording can use 5–15% battery per hour. A power bank is fine.",
        "Bring something to hold the phone rigidly: a suction or clamp window mount, painter's tape, or a non-slip pad.",
        "Book a window seat if you can. GPS needs a view of the sky, and the sidewall is the stiffest place to mount.",
        "Do the pre-flight calibration at home or at the gate, on a solid table. That takes about 20 minutes.",
    )),
    Section("calibration", "Calibration (4 positions)", listOf(
        "Calibration measures your gyro's own offset (bias). Without it the flight data can't be interpreted.",
        "Put the phone on a solid, level table and leave it alone. Don't touch the table, and nobody should walk heavily nearby.",
        "Position 1: screen up, with the phone's long edge pressed against the table edge or a heavy book.",
        "Position 2: screen up, turned 180° (top now points the other way), with the same edge against the same straight edge.",
        "Position 3: screen down, edge against the straight edge.",
        "Position 4: screen down, turned 180°.",
        "Each position counts only the seconds when the phone is truly still, about 5 minutes each. If the counter pauses, something is shaking.",
        "Turning exactly 180° matters. It makes the Earth's rotation cancel out of the bias. Calibration also measures that rotation directly, which is a ground-level test in its own right.",
        "Repeat after landing. Comparing before with after shows how much the bias drifted during the flight.",
    )),
    Section("drift", "Drift runs (optional, valuable)", listOf(
        "A drift run is 30+ minutes of the phone lying completely still. It shows how stable your gyro's bias is over time and against temperature.",
        "Do one before and/or after the flight, for example overnight at the hotel, with the phone screen up on a solid surface.",
    )),
    Section("placement", "Placing the phone in the aircraft", listOf(
        "Best: mounted against the window frame or cabin sidewall with a suction/clamp mount. The sidewall is the stiffest part of the cabin you can reach.",
        "Good: firmly clamped to the seat structure, but only where it can't come loose or get in anyone's way.",
        "Acceptable: on the tray table, taped down or on a non-slip pad, with the tray locked. Trays flex, and they must be stowed for takeoff and landing, so start the recording once you're at cruise.",
        "Never handheld. A held phone is useless for this measurement.",
        "The phone doesn't need to be level. It just has to keep the same orientation relative to the aircraft for the whole recording.",
        "Once it's placed, run the placement check. The app waits until the phone has been stable for 60 seconds.",
        "Don't touch the phone, the tray or the seat back during the recording. If you bump it, tap “I moved the phone” so the analysis can split the data there.",
        "Follow crew instructions and airline rules on devices at all times.",
    )),
    Section("flight", "During the flight", listOf(
        "Put the phone in airplane mode but leave Location on. GPS works in airplane mode on most phones.",
        "Record as much of the cruise as you can, ideally the whole flight if the phone is wall-mounted. Turns help, because they let the analysis find the aircraft's forward axis and separate signal from bias.",
        "Use battery-saver mode (a black screen) for long recordings. Recording carries on with the screen off.",
        "Live mode shows ground speed, what each model predicts, and a rough measured rate. The live 'measured' number is only a 5-minute average and needs the full analysis to mean anything.",
    )),
    Section("after", "After landing", listOf(
        "Do the post-flight calibration (the same 4 positions) as soon as you can, ideally within a few hours.",
        "Then tap Finish and Upload. Uploads only happen when you ask, and by default only on Wi-Fi.",
        "You can also Share the session file and analyze it yourself. The analysis software is open source.",
    )),
    Section("controls", "Control experiments", listOf(
        "Turn the phone 180° in its mount on a second flight, or halfway through a long flight (tap “I moved the phone”). A real rotation of the aircraft frame shows up on different sensor axes, while sensor bias stays on the same axes.",
        "Two phones mounted in different orientations on the same flight are an even stronger check.",
        "Stationary recordings on the ground are just as valuable. They test Earth rotation at your latitude.",
    )),
    Section("privacy", "Privacy and open source", listOf(
        "Recorded: raw motion sensors, pressure, GPS during the flight only, battery temperature, the flight details you enter, and phone model.",
        "Not recorded: your name, account, contacts or precise home location. Calibrations save only latitude rounded to 0.5°, and you can turn that off in Settings.",
        "A random install ID links your own sessions together so the same-phone bias can be modelled. It isn't tied to you.",
        "Uploaded data is released into the public domain (CC0) so anyone can reanalyze it. The app, server and analysis code are AGPL-3.0 open source.",
    )),
)

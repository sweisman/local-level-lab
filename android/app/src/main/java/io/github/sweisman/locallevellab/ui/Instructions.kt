// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

/** Participant instructions: keep synchronized with docs/PROTOCOL.md. */
data class Section(val key: String, val title: String, val body: List<String>)

val INSTRUCTIONS = listOf(
    Section("about", "What this measures", listOf(
        "An IMU (inertial measurement unit) measures turning and acceleration. This experiment records it resting on a solid surface in two opposite orientations.",
        "Reversal helps separate a signed external horizontal rotation from a constant sensor offset. Changing temperature, tilt and drift still matter.",
        "The analysis estimates the reversal signal without latitude or an expected rotation rate. Comparing sealed estimates across latitude is a later scientific step.",
        "NASA airborne analysis is the project's primary work. This stationary consumer experiment is independent and still needs physical sensitivity and uncertainty validation.",
    )),
    Section("ground", "Stationary A/B protocol", listOf(
        "Mark two positions 180° apart, same face up. Align a marked positive horizontal X or Y axis approximately toward true north in A; record how you aligned it and the uncertainty.",
        "Use a solid, level surface and secure loose cables. Let temperature settle. Create a stationary recording with location and device details; approximate or unknown location is acceptable for instrument controls.",
        "Record A–B–B–A twice. Default blocks last 30 still minutes: about four hours plus settling and turns. No duration guarantees a detection.",
        "Keep hands off during blocks. A notification announces completion. Open the app before starting the next block; turn only when A/B changes. Consecutive equal positions require no turn.",
        "Turn slowly, keeping the same face up. The analysis excludes 30 seconds at each block edge. Interrupted blocks remain saved; repeat a short block when prompted.",
        "Indoor GPS is unnecessary. Enter southern latitude and western longitude as negative. A magnetic compass gives magnetic north; use a true-north reference or record its uncertainty.",
    )),
    Section("calibration", "Instrument controls", listOf(
        "Use instrument-test sessions for stillness, known slow turns, temperature and link tests.",
        "Verify that independently imposed slow rotation survives with automatic zeroing off. A successful register readback alone is insufficient.",
        "Repeat on different days and compare independent units. Keep failures and null results. Do not qualify a sensor by matching an expected Earth-rate value.",
    )),
    Section("privacy", "Privacy and sharing", listOf(
        "New stationary sessions record raw IMU bytes, block timing, entered location/alignment, device details, notes and random linked identifiers. They require no flight information or continuous GPS.",
        "The Bluetooth address stays on the phone. Entered locations, serial labels and notes can identify you; omit or round private location details.",
        "Sharing exports an archive. Upload explicitly requires permanent public-release consent under CC0. Copies downloaded by others cannot be recalled.",
        "Historical archives retain their original GPS and flight metadata. They are never rewritten. No expected rotation value is shown during the new recording flow.",
    )),
)

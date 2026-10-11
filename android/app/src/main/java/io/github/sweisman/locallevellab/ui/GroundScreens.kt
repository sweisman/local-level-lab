// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import io.github.sweisman.locallevellab.Prefs
import io.github.sweisman.locallevellab.model.GroundProtocol
import io.github.sweisman.locallevellab.recording.Live
import io.github.sweisman.locallevellab.recording.RecorderService
import io.github.sweisman.locallevellab.recording.SessionStore
import org.json.JSONObject

@Composable
fun NewSessionScreen(nav: NavController, kind: String = "stationary") {
    val ctx = LocalContext.current
    if (!imuChosen(ctx)) {
        Page("New recording", nav) {
            Para("Choose and verify your IMU in Settings first.")
            Button({ nav.navigate("settings") }) { Text("Open Settings") }
        }
        return
    }
    if (kind == "bench") {
        Page("Instrument test", nav) {
            Para("Record stillness, reversals or a known slow turn to characterize your IMU.")
            Button({
                val s = SessionStore.create(ctx, JSONObject(), JSONObject().put("type", "solid_surface"), "bench")
                nav.navigate("session/${s.id}") { popUpTo("home") }
            }) { Text("Create instrument test") }
        }
        return
    }
    var fields by remember { mutableStateOf(mapOf("heading_true_deg" to "0", "heading_uncertainty_deg" to "10")) }
    var axis by remember { mutableStateOf("x") }
    var minutes by remember { mutableIntStateOf(Prefs(ctx).groundBlockMinutes) }
    var supported by remember { mutableStateOf(false) }
    val metadata = JSONObject().put("protocol", GroundProtocol.VERSION).put("axis", axis)
        .put("block_minutes", minutes).put("location_source", "participant_entered")
    var numbersValid = true
    for ((key, value) in fields) {
        if (value.isBlank()) continue
        if (key in listOf("latitude_deg", "longitude_deg", "altitude_m", "heading_true_deg", "heading_uncertainty_deg")) {
            val number = value.toDoubleOrNull()
            if (number == null || !number.isFinite()) numbersValid = false else metadata.put(key, number)
        } else metadata.put(key, value.trim())
    }
    Page("New stationary recording", nav, "ground") {
        Para("Put the IMU on a solid, level surface. Mark two opposite positions, A and B, with the same face up. Align the selected positive axis approximately toward true north in A.")
        Choice(listOf("x" to "Marked +X axis points north in A", "y" to "Marked +Y axis points north in A"), axis) { axis = it }
        for ((key, label) in listOf("latitude_deg" to "Latitude (optional, signed degrees)",
            "longitude_deg" to "Longitude (optional, signed degrees)", "altitude_m" to "Approximate altitude (m, optional)",
            "heading_true_deg" to "Axis direction in A (degrees from true north)",
            "heading_uncertainty_deg" to "Approximate direction uncertainty (degrees)",
            "alignment_method" to "How you found true north", "device_serial" to "IMU serial or label (optional)",
            "support_note" to "Surface / holder", "notes" to "Notes (public if uploaded)")) {
            OutlinedTextField(fields[key] ?: "", { fields = fields + (key to it) },
                label = { Text(label) }, modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp))
        }
        Para("Use a map or a known location; indoor GPS is not required. You may round coordinates. Enter southern latitude and western longitude as negative. Location and notes become public only if you consent to upload.", true)
        Stepper("Minutes per still block", minutes, 10..120, 10) { minutes = it; Prefs(ctx).groundBlockMinutes = it }
        Para("Eight blocks: A–B–B–A, then repeat. About ${minutes * 8 / 60.0} hours plus settling and turns. The same-position blocks require no turn. The duration is a development setting, not a promised detection threshold.")
        SwitchRow("The IMU has a solid, level support and two marked positions", supported) { supported = it }
        Button({
            val s = SessionStore.create(ctx, JSONObject(), JSONObject().put("type", "solid_surface"), "stationary", metadata)
            nav.navigate("session/${s.id}") { popUpTo("home") }
        }, Modifier.fillMaxWidth(), enabled = supported && numbersValid && GroundProtocol.valid(metadata)) { Text("Create recording") }
    }
}

@Composable
fun GroundRecordingScreen(id: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    val s = rememberSession(id) ?: return
    val target = s.manifest.getJSONObject("stationary").getInt("block_minutes") * 60.0
    val next = GroundProtocol.steps.firstOrNull { name ->
        (s.phases.lastOrNull { it.getString("name") == name }?.optDouble("still_s") ?: 0.0) < target }
    val active = live.sessionId == id && live.phase?.startsWith("ground.") == true
    val preview = rememberImuPreview()
    Page("Stationary reversals", nav, "ground") {
        ImuStatusPanel(live)
        Para("Same face up throughout. Keep the marked axis horizontal. Move only between blocks; the first and last 30 seconds will be excluded from the diagnostic.")
        if (active) {
            Text("Position ${live.phase!!.split('.')[1]} — recording", style = MaterialTheme.typography.headlineSmall)
            Para("Do not touch the IMU or its support.")
            Stat("Still time", "${fmtTime(live.stillS)} / ${fmtTime(target)}")
            LinearProgressIndicator(progress = { (live.stillS / target).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth())
            Para(if (live.isStill) "Still" else "Movement detected; raw data is still preserved.")
            OutlinedButton({ RecorderService.stop(ctx) }) { Text("Stop this block (saved as incomplete)") }
        } else if (next != null) {
            val i = GroundProtocol.steps.indexOf(next)
            Text("Block ${i + 1} of 8: position ${GroundProtocol.positions[i]}", style = MaterialTheme.typography.headlineSmall)
            Para(if (i == 0) "Place the marked positive axis toward true north in A."
                else if (GroundProtocol.positions[i] == GroundProtocol.positions[i-1]) "Stay in the same position; do not turn."
                else "Turn slowly by 180° to the other marked position, same face up. Let it settle before starting.")
            val level = preview.gravity[2] > 8.5f
            Button({ RecorderService.start(ctx, id, next, target) }, enabled = level && live.phase == null && live.imuConnected && live.imuConfigOk == true) { Text("Start position ${GroundProtocol.positions[i]}") }
            Para("The accelerometer checks which face is up; it does not verify north or an exact 180° turn. Use your holder marks.", true)
        } else {
            Para("All eight blocks are saved. Inspect completeness before interpreting a result.")
            Button({ nav.popBackStack() }) { Text("Back to recording") }
        }
        Para("No expected rotation value is shown. The analysis estimates the signed reversal signal before checking latitude.", true)
    }
}

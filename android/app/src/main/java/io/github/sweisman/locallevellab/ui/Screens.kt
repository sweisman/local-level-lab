// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.view.WindowManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import io.github.sweisman.locallevellab.Prefs
import io.github.sweisman.locallevellab.model.Transport
import io.github.sweisman.locallevellab.recording.Live
import io.github.sweisman.locallevellab.recording.RecorderService
import io.github.sweisman.locallevellab.recording.Session
import io.github.sweisman.locallevellab.recording.SessionStore
import io.github.sweisman.locallevellab.upload.UploadWorker
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// ---------- shared pieces ----------

@Composable
fun Page(title: String, nav: NavController?, help: String? = null, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (nav != null && nav.previousBackStackEntry != null) TextButton({ nav.popBackStack() }) { Text("‹ Back") }
            Text(title, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f))
            if (nav != null && help != null) TextButton({ nav.navigate("instructions?section=$help") }) { Text("Help") }
        }
        Spacer(Modifier.height(8.dp))
        content()
    }
}

@Composable
fun Para(text: String, muted: Boolean = false) =
    Text(text, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(vertical = 4.dp),
        color = if (muted) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface)

@Composable
fun Stat(label: String, value: String, big: Boolean = false) {
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.weight(1f))
        Text(value, fontFamily = FontFamily.Monospace, fontSize = if (big) 22.sp else 15.sp, fontWeight = if (big) FontWeight.Bold else null)
    }
}

fun fmtTime(s: Double): String {
    val t = s.toLong()
    return if (t >= 3600) "%d:%02d:%02d".format(t / 3600, t / 60 % 60, t % 60) else "%d:%02d".format(t / 60, t % 60)
}

@Composable
fun rememberSession(id: String): Session? {
    val live by Live.flow.collectAsStateWithLifecycle()
    val ctx = LocalContext.current
    // reload whenever a phase completes
    return remember(id, live.lastCompletedPhase, live.phase) { SessionStore.load(ctx, id) }
}

// ---------- consent & home ----------

@Composable
fun ConsentScreen(onDone: () -> Unit, nav: NavController) {
    val ctx = LocalContext.current
    val perms = buildList {
        add(Manifest.permission.ACCESS_FINE_LOCATION); add(Manifest.permission.ACCESS_COARSE_LOCATION)
        if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
    }.toTypedArray()
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        Prefs(ctx).consented = true
        onDone()
    }
    Page("Local Level Lab", null) {
        Para("A citizen-science instrument. A small motion sensor (IMU) records during a flight while your phone logs GPS, and open analysis tests whether the data fit a flat or spherical Earth, still or rotating.")
        INSTRUCTIONS.first { it.key == "privacy" }.body.forEach { Para("• $it") }
        Para("Location permission is used to record GPS during the flight (and an optional rounded latitude at calibration). Notifications show that a recording is running and remind you when to turn the IMU. Bluetooth access is asked for in Settings, when you choose the IMU.", muted = true)
        Spacer(Modifier.height(12.dp))
        Button({ launcher.launch(perms) }, Modifier.fillMaxWidth()) { Text("I understand. Continue") }
        TextButton({ nav.navigate("instructions") }) { Text("Read the full instructions first") }
    }
}

@Composable
fun HomeScreen(nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    val sessions = remember(live.lastCompletedPhase) { SessionStore.list(ctx) }
    Page("Local Level Lab", null) {
        if (live.phase != null && live.sessionId != null) {
            Card(Modifier.fillMaxWidth().clickable { nav.navigate("session/${live.sessionId}") }) {
                Column(Modifier.padding(12.dp)) {
                    Text("● Recording: ${live.phase}", color = MaterialTheme.colorScheme.error)
                    Text("${fmtTime(live.elapsedS)} — tap to open")
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        Button({ nav.navigate("new") }, Modifier.fillMaxWidth()) { Text("New flight session") }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
            OutlinedButton({ nav.navigate("instructions") }, Modifier.weight(1f)) { Text("Instructions") }
            OutlinedButton({ nav.navigate("settings") }, Modifier.weight(1f)) { Text("Settings") }
        }
        Text("Sessions", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 8.dp))
        if (sessions.isEmpty()) Para("None yet. Start with “New flight session”, then follow the steps.", muted = true)
        sessions.forEach { s ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable { nav.navigate("session/${s.id}") }) {
                Column(Modifier.padding(12.dp)) {
                    Text(s.title, fontWeight = FontWeight.SemiBold)
                    val up = s.local.optString("upload_id").let { if (it.isNotEmpty()) "uploaded" else if (s.finalized) "packaged" else "in progress" }
                    Text("${s.phases.size} phases · ${"%.1f".format(s.sizeBytes() / 1e6)} MB · $up",
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable
fun InstructionsScreen(section: String?, nav: NavController) {
    Page("Instructions", nav) {
        val list = if (section != null) INSTRUCTIONS.sortedByDescending { it.key == section } else INSTRUCTIONS
        list.forEach { sec ->
            Text(sec.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp, bottom = 4.dp),
                color = if (sec.key == section) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface)
            sec.body.forEach { Para(it) }
        }
    }
}

@Composable
fun SettingsScreen(nav: NavController) {
    val ctx = LocalContext.current
    val p = remember { Prefs(ctx) }
    var url by remember { mutableStateOf(p.serverUrl) }
    var unmetered by remember { mutableStateOf(p.unmeteredOnly) }
    var calLat by remember { mutableStateOf(p.shareCalLatitude) }
    var calMin by remember { mutableIntStateOf(p.calPositionMinutes) }
    var driftMin by remember { mutableIntStateOf(p.driftMinutes) }
    Page("Settings", nav) {
        ImuSettings(nav)
        HorizontalDivider(Modifier.padding(vertical = 12.dp))
        OutlinedTextField(url, { url = it; p.serverUrl = it }, label = { Text("Upload server URL") }, singleLine = true,
            modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri))
        Para("Uploads go only to this address, and only when you tap Upload. It must start with https://.", muted = true)
        SwitchRow("Upload on Wi-Fi only", unmetered) { unmetered = it; p.unmeteredOnly = it }
        SwitchRow("Save calibration latitude (rounded to 0.5°)", calLat) { calLat = it; p.shareCalLatitude = it }
        Para("The latitude lets calibrations test the Earth-rotation models at your location. Rounding keeps it to roughly 50 km.", muted = true)
        Stepper("Calibration minutes per position", calMin, 2..15) { calMin = it; p.calPositionMinutes = it }
        Stepper("Drift run minutes", driftMin, 10..240, step = 10) { driftMin = it; p.driftMinutes = it }
        HorizontalDivider(Modifier.padding(vertical = 12.dp))
        Para("Install ID: ${p.installId}", muted = true)
        Para("Local Level Lab is free software under the GNU AGPL v3. Uploaded data is public domain (CC0).", muted = true)
    }
}

@Composable
fun SwitchRow(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(label, Modifier.weight(1f)); Switch(value, onChange)
    }
}

@Composable
fun Stepper(label: String, value: Int, range: IntRange, step: Int = 1, onChange: (Int) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(label, Modifier.weight(1f))
        TextButton({ onChange((value - step).coerceIn(range)) }) { Text("−") }
        Text("$value", fontFamily = FontFamily.Monospace)
        TextButton({ onChange((value + step).coerceIn(range)) }) { Text("+") }
    }
}

// ---------- new session ----------

@Composable
fun Choice(options: List<Pair<String, String>>, value: String, onChange: (String) -> Unit) {
    Column {
        options.forEach { (key, label) ->
            Row(Modifier.fillMaxWidth().selectable(value == key, onClick = { onChange(key) }).padding(vertical = 2.dp),
                verticalAlignment = Alignment.CenterVertically) {
                RadioButton(value == key, { onChange(key) }); Text(label)
            }
        }
    }
}

@Composable
fun NewSessionScreen(nav: NavController, kind: String = "flight") {
    val ctx = LocalContext.current
    val today = remember { SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()) }
    val f = remember { mutableStateOf(mapOf("date" to today, "seat_position" to "window")) }
    if (!imuChosen(ctx)) {
        Page("New session", nav) {
            Para("Choose your IMU in Settings first. The recording comes from the IMU; the phone logs GPS and runs the dashboard.")
            Button({ nav.navigate("settings") }, Modifier.fillMaxWidth()) { Text("Open Settings") }
        }
        return
    }
    if (kind == "bench") {
        Page("Bench capture", nav) {
            Para("A stationary recording of the IMU on a solid table, for checking the link, the noise and the bias stability (lll bench). Nothing flight-related is recorded.")
            Button({
                val s = SessionStore.create(ctx, JSONObject().put("notes", "bench capture"), JSONObject().put("type", "bench"), kind = "bench")
                nav.navigate("session/${s.id}") { popUpTo("home") }
            }, Modifier.fillMaxWidth()) { Text("Create bench session") }
        }
        return
    }
    var mount by remember { mutableStateOf("window") }
    var orientation by remember { mutableStateOf("") }
    var rotated by remember { mutableStateOf(false) }
    @Composable
    fun field(key: String, label: String, kb: KeyboardType = KeyboardType.Text) =
        OutlinedTextField(f.value[key] ?: "", { f.value = f.value + (key to it) }, label = { Text(label) }, singleLine = true,
            modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp), keyboardOptions = KeyboardOptions(keyboardType = kb))
    Page("New flight session", nav, help = "before") {
        field("airline", "Airline (e.g. United)")
        field("flight_number", "Flight number (e.g. UA 123)")
        field("date", "Date (YYYY-MM-DD)")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.weight(1f)) { field("origin", "From (IATA)") }
            Box(Modifier.weight(1f)) { field("destination", "To (IATA)") }
        }
        field("aircraft_type", "Aircraft type, if known (e.g. A321)")
        field("seat", "Seat where the IMU is logging (e.g. 23A)")
        Choice(listOf("window" to "Window", "middle" to "Middle", "aisle" to "Aisle"), f.value["seat_position"] ?: "window") {
            f.value = f.value + ("seat_position" to it)
        }
        Text("How will the IMU be mounted?", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
        Choice(listOf(
            "window" to "Window frame mount (best)", "sidewall" to "Sidewall mount", "seat_frame" to "Clamped to seat structure",
            "tray" to "Fixed to the tray table (cruise only)", "other" to "Other",
        ), mount) { mount = it }
        OutlinedTextField(orientation, { orientation = it }, label = { Text("Orientation note (e.g. label up, USB port forward)") },
            modifier = Modifier.fillMaxWidth())
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(rotated, { rotated = it }); Text("This is a 180°-rotated control run")
        }
        field("notes", "Notes (optional)")
        Spacer(Modifier.height(12.dp))
        Button({
            val flight = JSONObject()
            listOf("airline", "flight_number", "date", "origin", "destination", "aircraft_type", "seat", "seat_position", "notes")
                .forEach { flight.put(it, (f.value[it] ?: "").trim().let { v -> if (it == "seat") v.uppercase() else v }) }
            val m = JSONObject().put("type", mount).put("orientation_note", orientation.trim()).put("rotated_180_control", rotated)
            val s = SessionStore.create(ctx, flight, m)
            nav.navigate("session/${s.id}") { popUpTo("home") }
        }, Modifier.fillMaxWidth(), enabled = (f.value["seat"] ?: "").isNotBlank()) { Text("Create session") }
        if ((f.value["seat"] ?: "").isBlank()) Para("Enter the seat to continue.", muted = true)
    }
}

// ---------- session checklist ----------

@Composable
fun SessionScreen(id: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    var refresh by remember { mutableIntStateOf(0) }
    val s = remember(id, live.lastCompletedPhase, live.phase, refresh) { SessionStore.load(ctx, id) } ?: run {
        Page("Session", nav) { Para("Session not found.") }; return
    }
    var confirmDelete by remember { mutableStateOf(false) }
    val recordingHere = live.phase != null && live.sessionId == id
    Page(s.title, nav, help = "about") {
        if (recordingHere) {
            Button({ nav.navigate(if (live.phase == "flight") "record/$id" else if (live.phase == "placement_check") "placement/$id"
                else if (live.phase!!.startsWith("cal_")) "cal/$id/${live.phase!!.substringBefore('.').removePrefix("cal_")}" else "still/$id/${live.phase}") },
                Modifier.fillMaxWidth()) { Text("● Recording ${live.phase} — open") }
        }
        if (s.manifest.optString("kind") == "bench") {
            Step("1. Calibration", s.manifest.getJSONObject("quality").optBoolean("cal_pre"), "About 25 min on a solid table") { nav.navigate("cal/$id/pre") }
            Step("2. Bench recording", s.hasPhase("bench"), "${Prefs(ctx).driftMinutes} min lying still (30+ for a quality tier)") { nav.navigate("still/$id/bench") }
        } else {
        Step("1. Pre-flight calibration", s.manifest.getJSONObject("quality").optBoolean("cal_pre"), "About 25 min on a solid table") { nav.navigate("cal/$id/pre") }
        Step("2. Pre-flight drift run (optional)", s.hasPhase("drift_pre"), "${Prefs(ctx).driftMinutes} min lying still") { nav.navigate("still/$id/drift_pre") }
        Step("3. Mount the IMU + check stability", s.hasPhase("placement_check"), "In the aircraft, once it's mounted") { nav.navigate("placement/$id") }
        Step("4. Flight recording", s.hasPhase("flight"), "Starts after the placement check") { nav.navigate(if (s.hasPhase("placement_check")) "record/$id" else "placement/$id") }
        Step("5. Post-flight calibration", s.manifest.getJSONObject("quality").optBoolean("cal_post"), "Same 7 placements, after landing") { nav.navigate("cal/$id/post") }
        Step("6. Post-flight drift run (optional)", s.hasPhase("drift_post"), "${Prefs(ctx).driftMinutes} min lying still") { nav.navigate("still/$id/drift_post") }
        }
        HorizontalDivider(Modifier.padding(vertical = 12.dp))
        Text("7. Finish", style = MaterialTheme.typography.titleMedium)
        val err = s.local.optString("upload_error")
        when {
            s.local.optString("upload_id").isNotEmpty() -> Para("Uploaded ✓ (server id ${s.local.optString("upload_id").take(8)})")
            err.isNotEmpty() -> Para("Upload problem: $err", muted = true)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            Button({ UploadWorker.enqueue(ctx, id); refresh++ }, Modifier.weight(1f), enabled = !recordingHere && (s.hasPhase("flight") || s.hasPhase("bench"))) { Text("Upload") }
            OutlinedButton({ share(ctx, s); refresh++ }, Modifier.weight(1f), enabled = !recordingHere) { Text("Share file") }
        }
        Para("Uploading queues the session and sends it when the network allows (Settings: Wi-Fi only = ${Prefs(ctx).unmeteredOnly}).", muted = true)
        TextButton({ confirmDelete = true }, enabled = !recordingHere) { Text("Delete session", color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.height(8.dp))
        Para("Phases recorded: " + s.phases.joinToString { it.getString("name") }.ifEmpty { "none" }, muted = true)
    }
    if (confirmDelete) AlertDialog(
        onDismissRequest = { confirmDelete = false },
        confirmButton = { TextButton({ SessionStore.delete(s); confirmDelete = false; nav.popBackStack() }) { Text("Delete") } },
        dismissButton = { TextButton({ confirmDelete = false }) { Text("Cancel") } },
        title = { Text("Delete this session?") }, text = { Text("The raw data on this phone will be removed. Data already uploaded stays on the server.") },
    )
}

@Composable
fun Step(title: String, done: Boolean, hint: String, onClick: () -> Unit) {
    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable(onClick = onClick)) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.SemiBold)
                Text(hint, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
            }
            Text(if (done) "✓ done" else "›", color = if (done) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

fun share(ctx: Context, s: Session) {
    val zip = SessionStore.finalize(s)
    val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".files", zip)
    ctx.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("application/zip")
        .putExtra(Intent.EXTRA_STREAM, uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION), "Share session"))
}

// ---------- calibration & drift ----------

private val POSITIONS = listOf(
    Triple("up0", "Label UP", "Lay the IMU label-up on a solid table, one long side pressed against a straight edge (a heavy book or the table edge)."),
    Triple("up180", "Label UP, turned 180°", "Turn the IMU 180° so its other end points the same way the first end did, with the same long side against the same straight edge."),
    Triple("down0", "Label DOWN", "Turn the IMU over, label down, long side against the straight edge."),
    Triple("down180", "Label DOWN, turned 180°", "Turn it 180°, still label down, side against the straight edge."),
)

@Composable
fun CalibrationScreen(id: String, which: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    val s = rememberSession(id) ?: return
    val target = Prefs(ctx).calPositionMinutes * 60.0
    val prefix = "cal_$which"
    val steps = SessionStore.CAL_STEPS
    fun len(step: String) = SessionStore.calStepLength(step)
    fun doneOk(step: String) = s.phases.any { it.getString("name") == "$prefix.$step" && it.optDouble("still_s") >= 0.8 * target * len(step) }
    fun pos(step: String) = POSITIONS.first { it.first == step.substringBefore('.') }
    val activeStep = live.phase?.takeIf { it.startsWith("$prefix.") && live.sessionId == id }?.substringAfter('.')
    val next = steps.firstOrNull { !doneOk(it) }
    val g = rememberImuPreview().gravity
    Page(if (which == "pre") "Pre-flight calibration" else "Post-flight calibration", nav, help = "calibration") {
        ImuStatusPanel(live)
        Para("Seven placements: each position twice, in mirror order, so the analysis can measure and remove any slow drift. The middle one is a single double-length stay.", muted = true)
        steps.forEachIndexed { i, step ->
            Stat("${i + 1}. ${pos(step).second}" + if (len(step) > 1) " (double)" else "",
                if (doneOk(step)) "✓" else if (activeStep == step) "recording" else "–")
        }
        Spacer(Modifier.height(12.dp))
        if (activeStep != null) {
            Text(pos(activeStep).second, style = MaterialTheme.typography.titleLarge)
            Para("Don't touch the IMU or the table. Only still seconds count.")
            val t = target * len(activeStep)
            LinearProgressIndicator(progress = { (live.stillS / t).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
            Stat("Still time", "${fmtTime(live.stillS)} / ${fmtTime(t)}", big = true)
            Stat("Status", if (live.isStill) "still ✓" else "MOVING — paused")
            Stat("Accel noise", "%.3f m/s²".format(live.accelSd))
            Stat("Gyro noise", "%.3f °/s".format(live.gyroSdDps))
            OutlinedButton({ RecorderService.stop(ctx) }, Modifier.fillMaxWidth().padding(top = 8.dp)) { Text("Stop (you'll need to redo this position)") }
        } else if (next != null) {
            Text("Next: ${pos(next).second}" + if (next.endsWith(".b")) " (second visit)" else "", style = MaterialTheme.typography.titleLarge)
            Para(pos(next).third)
            val wantUp = next.startsWith("up")
            val ok = if (wantUp) g[2] > 8.5f else g[2] < -8.5f
            Para(if (ok) "Orientation looks right ✓" else if (!live.imuConnected) "Waiting for the IMU to connect…"
                else "Waiting for the IMU to be label-${if (wantUp) "up" else "down"} and flat…", muted = !ok)
            Para("After you tap Start, keep your hands off. The analysis ignores the first and last 10 s of each position while the table settles.", muted = true)
            Button({ RecorderService.start(ctx, id, "$prefix.$next", target * len(next)) }, Modifier.fillMaxWidth(), enabled = ok && live.phase == null && live.imuConnected) {
                Text("Start placement ${steps.indexOf(next) + 1} of ${steps.size}")
            }
        } else {
            Text("Calibration complete ✓", style = MaterialTheme.typography.titleLarge)
            Button({ nav.popBackStack() }, Modifier.fillMaxWidth()) { Text("Back to session") }
        }
    }
}

@Composable
fun DriftScreen(id: String, name: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    val s = rememberSession(id) ?: return
    val target = Prefs(ctx).driftMinutes * 60.0
    val active = live.phase == name && live.sessionId == id
    rememberImuPreview()
    Page(if (name == "bench") "Bench recording" else "Drift run", nav, help = "drift") {
        Para("Lay the IMU label-up on a solid surface where nothing will disturb it. The phone's screen can turn off; recording carries on.")
        ImuStatusPanel(live)
        if (active) {
            LinearProgressIndicator(progress = { (live.stillS / target).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
            Stat("Still time", "${fmtTime(live.stillS)} / ${fmtTime(target)}", big = true)
            Stat("Status", if (live.isStill) "still ✓" else "MOVING — paused")
            OutlinedButton({ RecorderService.stop(ctx) }, Modifier.fillMaxWidth()) { Text("Stop early") }
            ActivityFeed(live)
        } else if (s.hasPhase(name)) {
            Para("Recorded ✓")
            Button({ nav.popBackStack() }, Modifier.fillMaxWidth()) { Text("Back to session") }
        } else {
            Button({ RecorderService.start(ctx, id, name, target) }, Modifier.fillMaxWidth(), enabled = live.phase == null && live.imuConnected) {
                Text(if (live.imuConnected) "Start recording" else "Waiting for the IMU…")
            }
        }
    }
}

// ---------- placement & flight ----------

@Composable
fun PlacementScreen(id: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    val active = live.phase == "placement_check" && live.sessionId == id
    rememberImuPreview()
    Page("Placement check", nav, help = "placement") {
        ImuStatusPanel(live)
        INSTRUCTIONS.first { it.key == "placement" }.body.take(4).forEach { Para("• $it") }
        Spacer(Modifier.height(8.dp))
        if (!active) {
            Button({ RecorderService.start(ctx, id, "placement_check") }, Modifier.fillMaxWidth(), enabled = live.phase == null && live.imuConnected) {
                Text(if (live.imuConnected) "IMU is mounted. Start the check" else "Waiting for the IMU…")
            }
        } else {
            Stat("Stable for", "${live.stillStreakS.toInt()} / 60 s", big = true)
            LinearProgressIndicator(progress = { (live.stillStreakS / 60.0).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
            Stat("Accel noise", "%.3f m/s²".format(live.accelSd))
            Stat("Gyro noise", "%.3f °/s".format(live.gyroSdDps))
            Stat("Gravity axis", live.gravityAxis)
            Stat("GPS", if (live.hasFix) "fix, ${live.sats} sats" else "searching…")
            Para("Light vibration is normal. If the counter keeps resetting, the IMU isn't held firmly enough.", muted = true)
            Button({ RecorderService.start(ctx, id, "flight"); nav.navigate("record/$id") { popUpTo("session/$id") } },
                Modifier.fillMaxWidth(), enabled = live.stillStreakS >= 60) { Text("Start flight recording") }
            TextButton({ RecorderService.stop(ctx) }) { Text("Cancel check") }
        }
    }
}

@Composable
fun RecordScreen(id: String, nav: NavController) {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    var saver by remember { mutableStateOf(false) }
    var confirmStop by remember { mutableStateOf(false) }
    val active = live.phase == "flight" && live.sessionId == id
    val view = LocalView.current
    val activity = ctx as? Activity
    DisposableEffect(saver, active) {
        view.keepScreenOn = active && !saver
        activity?.window?.let { w ->
            w.attributes = w.attributes.apply {
                screenBrightness = if (saver) 0.01f else WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE
            }
        }
        onDispose {
            view.keepScreenOn = false
            activity?.window?.let { w -> w.attributes = w.attributes.apply { screenBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE } }
        }
    }
    LaunchedEffect(live.lastCompletedPhase) { if (live.lastCompletedPhase == "flight") nav.popBackStack() }

    if (saver && active) {
        Box(Modifier.fillMaxSize().background(Color.Black).clickable { saver = false }, contentAlignment = Alignment.Center) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(8.dp).background(Color(0xFF5A1E1E), CircleShape))
                Spacer(Modifier.size(8.dp))
                Text(fmtTime(live.elapsedS), color = Color(0xFF3A3A3A), fontFamily = FontFamily.Monospace)
            }
        }
        return
    }
    Page("Flight recording", nav, help = "flight") {
        if (!active) {
            Para("Not recording. Start from the placement check so stability is confirmed first.")
            Button({ nav.navigate("placement/$id") }, Modifier.fillMaxWidth()) { Text("Go to placement check") }
            return@Page
        }
        Stat("Elapsed", fmtTime(live.elapsedS), big = true)
        live.activity.firstOrNull()?.let { Text(it, fontFamily = FontFamily.Monospace, fontSize = 13.sp) }
        TurnReminderCard(live, ctx)
        ImuStatusPanel(live)
        if (live.shiftWarning) Para("⚠ A placement shift or turn was logged. The analysis splits the data there.", muted = false)
        Stat("GPS", if (live.hasFix) "%d sats · ±%.0f m".format(live.sats, live.hAccM) else "searching… (window seat helps)")
        Stat("Ground speed", "%.0f km/h".format(live.speedMps * 3.6))
        Stat("Altitude", "%.0f m".format(live.altM))
        Stat("Track", "%.0f°".format(live.bearingDeg))
        HorizontalDivider(Modifier.padding(vertical = 8.dp))
        Text("Predicted rotation of local level", style = MaterialTheme.typography.titleSmall)
        Stat("Curvature only (transport)", "%.2f °/h · %.2f°".format(live.transportDph, live.transportAccumDeg))
        Transport.Model.entries.forEach { m ->
            Stat(m.label, "%.2f °/h · %.2f°".format(live.predictedDph[m] ?: 0.0, live.accumulatedDeg[m] ?: 0.0))
        }
        Stat("Measured (5-min mean, rough)", live.measuredDph?.let { "%.1f °/h".format(it) } ?: "needs pre-flight calibration")
        Para("Rate · accumulated angle so far. The live 'measured' value includes aircraft manoeuvres and sensor drift. Only the full analysis is meaningful.", muted = true)
        HorizontalDivider(Modifier.padding(vertical = 8.dp))
        Stat("Stability", "accel %.2f m/s² · gyro %.2f °/s".format(live.accelSd, live.gyroSdDps))
        ActivityFeed(live)
        Spacer(Modifier.height(12.dp))
        Button({ saver = true }, Modifier.fillMaxWidth()) { Text("Battery saver (black screen)") }
        OutlinedButton({ RecorderService.event(ctx, "placement_shift", "user reported") }, Modifier.fillMaxWidth().padding(top = 8.dp)) {
            Text("I moved / bumped the IMU")
        }
        TextButton({ confirmStop = true }, Modifier.padding(top = 8.dp)) { Text("Stop recording", color = MaterialTheme.colorScheme.error) }
    }
    if (confirmStop) AlertDialog(
        onDismissRequest = { confirmStop = false },
        confirmButton = { TextButton({ RecorderService.stop(ctx); confirmStop = false }) { Text("Stop") } },
        dismissButton = { TextButton({ confirmStop = false }) { Text("Keep recording") } },
        title = { Text("Stop the flight recording?") },
        text = { Text("Afterwards, do the post-flight calibration as soon as you can.") },
    )
}

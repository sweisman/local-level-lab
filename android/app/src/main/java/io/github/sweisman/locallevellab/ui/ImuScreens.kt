// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import io.github.sweisman.locallevellab.Prefs
import io.github.sweisman.locallevellab.recording.Live
import io.github.sweisman.locallevellab.recording.LiveState
import io.github.sweisman.locallevellab.recording.RecorderService
import io.github.sweisman.locallevellab.recording.imu.Variant

fun bluetoothPermissions(): Array<String> =
    if (Build.VERSION.SDK_INT >= 31) arrayOf(Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN)
    else arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)

fun hasBluetoothPermissions(ctx: Context) =
    bluetoothPermissions().all { ContextCompat.checkSelfPermission(ctx, it) == PackageManager.PERMISSION_GRANTED }

fun imuChosen(ctx: Context) = Prefs(ctx).let { it.imuVariant != null && it.imuAddress.isNotEmpty() }

/** Keeps the IMU link up while a screen that previews its orientation is visible. */
@Composable
fun rememberImuPreview(): LiveState {
    val ctx = LocalContext.current
    val live by Live.flow.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) { if (imuChosen(ctx) && hasBluetoothPermissions(ctx)) RecorderService.monitor(ctx) }
    return live
}

// ---------- Settings: choosing and configuring the IMU ----------

@SuppressLint("MissingPermission")  // guarded by hasBluetoothPermissions
@Composable
fun ImuSettings(nav: androidx.navigation.NavController) {
    val ctx = LocalContext.current
    val p = remember { Prefs(ctx) }
    val live by Live.flow.collectAsStateWithLifecycle()
    var variant by remember { mutableStateOf(p.imuVariant ?: Variant.SPP) }
    var chosen by remember { mutableStateOf(p.imuName.ifEmpty { p.imuAddress }) }
    var rate by remember { mutableIntStateOf(p.imuRateHz) }
    var range by remember { mutableIntStateOf(p.imuGyroRangeDps) }
    var accRange by remember { mutableIntStateOf(p.imuAccelRangeG) }
    var permOk by remember { mutableStateOf(hasBluetoothPermissions(ctx)) }
    var turnMin by remember { mutableIntStateOf(p.indexAlertMinutes) }
    var motions by remember { mutableStateOf(p.turnMotions) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permOk = hasBluetoothPermissions(ctx) }
    val adapter = remember { ctx.getSystemService(BluetoothManager::class.java)?.adapter }

    if (live.phase != null || p.activePhase != null) {
        Para("Stop recording before changing instrument settings.")
        return
    }
    Text("IMU (WitMotion WT901)", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 4.dp))
    Choice(listOf(Variant.SPP.key to "ICM-42605, Bluetooth 2.0 (pair it in Android settings first, PIN usually 1234)",
        Variant.BLE.key to "MPU9250, Bluetooth LE 5.0"), variant.key) { variant = Variant.of(it)!! }
    if (!permOk) {
        Button({ launcher.launch(bluetoothPermissions()) }, Modifier.fillMaxWidth()) { Text("Allow Bluetooth access") }
        return
    }
    if (adapter == null || !adapter.isEnabled) { Para("Turn Bluetooth on to choose the IMU.", muted = true); return }

    fun choose(address: String, name: String) {
        p.imuAddress = address; p.imuName = name; p.imuVariant = variant
        p.unitId(address)
        chosen = name.ifEmpty { address }
        RecorderService.configure(ctx)
    }

    if (variant == Variant.SPP) {
        val bonded = remember(permOk) { adapter.bondedDevices?.toList().orEmpty() }
        Para("Paired devices:", muted = true)
        if (bonded.isEmpty()) Para("None. Pair the IMU in Android's Bluetooth settings, then come back.", muted = true)
        bonded.forEach { d ->
            Text("${d.name ?: "unnamed"}", Modifier.fillMaxWidth().clickable { choose(d.address, d.name ?: "") }.padding(vertical = 8.dp))
        }
    } else {
        val found = remember { mutableStateListOf<Pair<String, String>>() }
        var scanning by remember { mutableStateOf(false) }
        DisposableEffect(scanning) {
            val scanner = adapter.bluetoothLeScanner
            val cb = object : ScanCallback() {
                override fun onScanResult(type: Int, r: ScanResult) {
                    val name = r.device.name ?: return
                    if (found.none { it.first == r.device.address }) found += r.device.address to name
                }
            }
            if (scanning) scanner?.startScan(cb)
            onDispose { if (scanning) runCatching { scanner?.stopScan(cb) } }
        }
        LaunchedEffect(scanning) { if (scanning) { kotlinx.coroutines.delay(12_000); scanning = false } }
        OutlinedButton({ found.clear(); scanning = true }, Modifier.fillMaxWidth(), enabled = !scanning) {
            Text(if (scanning) "Scanning…" else "Scan for the IMU")
        }
        found.forEach { (addr, name) ->
            Text(name, Modifier.fillMaxWidth().clickable { scanning = false; choose(addr, name) }.padding(vertical = 8.dp))
        }
    }
    Stat("Chosen", chosen.ifEmpty { "none" })
    Stat("Link", live.imuStatus)
    Stat("Settings verified", when (live.imuConfigOk) { true -> "yes ✓"; false -> "NO"; null -> "–" })
    Text("Output rate", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
    Choice(listOf("50" to "50 Hz", "100" to "100 Hz (recommended)", "200" to "200 Hz (serial link may not keep up)"), "$rate") {
        rate = it.toInt(); p.imuRateHz = rate
    }
    Text("Gyro range (test finer scaling on the bench first)", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
    Choice(listOf("2000" to "±2000 °/s: 220 °/h per count (default)", "1000" to "±1000 °/s: 110 °/h per count",
        "500" to "±500 °/s: 55 °/h per count", "250" to "±250 °/s: 27 °/h per count (turn the IMU slowly)"), "$range") {
        range = it.toInt(); p.imuGyroRangeDps = range
    }
    Para("Finer counts measure slow rotation better, but a quick hand turn can then exceed the range and that turn can't be used. Check the setting with a bench capture: the analysis decodes with the range the IMU reports back, and flags any difference.", muted = true)
    Text("Accelerometer range", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
    Choice(listOf("16" to "±16 g (default)", "8" to "±8 g", "4" to "±4 g (finer plumb line; enough for a cabin)", "2" to "±2 g"), "$accRange") {
        accRange = it.toInt(); p.imuAccelRangeG = accRange
    }
    OutlinedButton({ RecorderService.configure(ctx) }, Modifier.fillMaxWidth(), enabled = chosen.isNotEmpty()) {
        Text("Write and verify IMU settings")
    }
    Para("The app turns off the IMU's automatic gyro zeroing, which would otherwise erase the Earth's rotation, and turns off its own attitude outputs. It checks the settings again at every recording.", muted = true)

    HorizontalDivider(Modifier.padding(vertical = 12.dp))
    Text("During long recordings", style = MaterialTheme.typography.titleMedium)
    Stepper("Remind me to turn the IMU every (min, 0 = off)", turnMin, 0..240, step = 15) { turnMin = it; p.indexAlertMinutes = it }
    Text("Turns my mount allows", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 4.dp))
    Choice(listOf("plane180" to "Turn it to face the opposite way, same side up (best)",
        "both" to "Either kind", "flip" to "Only turning it upside down (much less useful)"), motions) {
        motions = it; p.turnMotions = it
    }
    Para("Turning the IMU to face the opposite way, keeping the same side up, moves the Earth's and the aircraft's rotation onto different sensor axes while the sensor's own bias stays put. On a straight route this is what makes the flight count. Turning it upside down helps much less, because gravity then sits on a different axis and the gyro's gravity-dependent error changes too. Each turn you confirm is logged and measured by the gyro.", muted = true)
    val pm = ctx.getSystemService(PowerManager::class.java)
    if (!pm.isIgnoringBatteryOptimizations(ctx.packageName)) {
        OutlinedButton({
            ctx.startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:${ctx.packageName}")))
        }, Modifier.fillMaxWidth()) { Text("Let recording run with the screen off") }
        Para("Some phones stop background apps to save battery. This exemption keeps the recording going with the screen off.", muted = true)
    } else Para("Background recording allowed ✓", muted = true)
    HorizontalDivider(Modifier.padding(vertical = 12.dp))
    Text("Bench tests (see docs/BENCH.md)", style = MaterialTheme.typography.titleMedium)
    TextButton({ nav.navigate("new?kind=bench") }) { Text("New bench session (stationary test of the IMU)") }
    var autoOn by remember { mutableStateOf(p.benchAutoZeroOn) }
    SwitchRow("Next bench session: auto-zero ON (polarity test)", autoOn) { autoOn = it; p.benchAutoZeroOn = it }
    Para("Only for a bench session made while this is on. Compare it with one made with it off: with auto-zero on, the Earth's rotation should vanish. Flights always force it off.", muted = true)
    OutlinedButton({ RecorderService.dropLink(ctx) }, Modifier.fillMaxWidth()) { Text("Disconnect test: drop the link, reconnect in 5 s") }
}

// ---------- dashboard pieces ----------

@Composable
fun ImuStatusPanel(live: LiveState) {
    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(Modifier.padding(12.dp)) {
            Stat("IMU link", if (live.imuConnected) "connected · %.0f Hz".format(live.imuRateHz) else live.imuStatus)
            if (live.phase != null) Stat("Logged", "%.1f MB · %d drops · %d bad frames".format(live.imuBytes / 1e6, live.imuDrops, live.imuBadChecksums))
            Stat("IMU battery", live.imuVolt?.let { "%.2f V".format(it) } ?: "–")
            Stat("IMU temperature", live.imuTempC?.let { "%.1f °C".format(it) } ?: "–")
            Stat("Phone battery", live.phoneBatteryPct?.let { "$it %" + if (live.phoneCharging) " · charging" else "" } ?: "–")
            if (live.imuConfigOk == false) Text("⚠ IMU settings not verified", color = MaterialTheme.colorScheme.error)
        }
    }
}

@Composable
fun TurnReminderCard(live: LiveState, ctx: Context) {
    val due = live.nextTurnInS ?: return
    val motions = remember { Prefs(ctx).turnMotions }
    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(Modifier.padding(12.dp)) {
            if (live.turnDue) {
                Text("Time to turn the IMU", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary, fontSize = 18.sp)
                Para(when (motions) {
                    "plane180" -> "Slowly, over about 5 seconds, turn it to face the opposite way, keeping the same side up. Fix it firmly again, then tap the button."
                    "flip" -> "Slowly, over about 5 seconds, turn it upside down in its mount. Fix it firmly again, then tap the button."
                    else -> "Slowly, over about 5 seconds, turn it to face the opposite way with the same side up (best), or turn it upside down. Fix it firmly again, then tap what you did."
                })
            } else Stat("Next turn reminder", fmtTime(maxOf(0.0, due)))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                if (motions != "flip") OutlinedButton({ RecorderService.turnDone(ctx, "plane180") }, Modifier.weight(1f)) { Text("Turned 180°") }
                if (motions != "plane180") OutlinedButton({ RecorderService.turnDone(ctx, "flip") }, Modifier.weight(1f)) { Text("Flipped") }
            }
            if (live.turnDue) TextButton({ RecorderService.turnDone(ctx, "skip") }) { Text("Skip this one") }
        }
    }
}

@Composable
fun ActivityFeed(live: LiveState, lines: Int = 8) {
    if (live.activity.isEmpty()) return
    Text("Activity", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
    live.activity.take(lines).forEach {
        Text(it, fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

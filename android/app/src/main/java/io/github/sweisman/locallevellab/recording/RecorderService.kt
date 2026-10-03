// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording

import android.Manifest
import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.location.GnssStatus
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.PowerManager
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import io.github.sweisman.locallevellab.LllApp
import io.github.sweisman.locallevellab.Prefs
import io.github.sweisman.locallevellab.R
import io.github.sweisman.locallevellab.model.Transport
import io.github.sweisman.locallevellab.recording.imu.ImuLink
import io.github.sweisman.locallevellab.recording.imu.Variant
import io.github.sweisman.locallevellab.recording.imu.WitConfig
import io.github.sweisman.locallevellab.recording.imu.WitParser
import io.github.sweisman.locallevellab.ui.MainActivity
import kotlinx.coroutines.flow.update
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedOutputStream
import java.io.BufferedWriter
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStreamWriter
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.GZIPOutputStream
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.sin

/** One gzip CSV member appended to a stream file. Values are written exactly as delivered. */
private class CsvGz(file: File, header: String) {
    private val w = BufferedWriter(OutputStreamWriter(GZIPOutputStream(FileOutputStream(file, true), 1 shl 16), Charsets.US_ASCII), 1 shl 16)
    var rows = 0L; private set

    init { w.write(header); w.write("\n") }

    fun row(t: Long, vararg v: String) {
        w.write(t.toString())
        for (s in v) { w.write(","); w.write(s) }
        w.write("\n")
        rows++
    }

    fun close() = w.close()
}

/**
 * imu.bin.gz: every Bluetooth read, verbatim, as a record `[int64 arrival_ns][uint16 length][bytes]`,
 * little-endian. One gzip member is appended per recording phase. See docs/FORMAT.md.
 */
private class ImuWriter(file: File) {
    private val out = BufferedOutputStream(GZIPOutputStream(FileOutputStream(file, true), 1 shl 16), 1 shl 16)
    private val head = ByteBuffer.allocate(10).order(ByteOrder.LITTLE_ENDIAN)
    var bytes = 0L; private set

    fun record(arrivalNs: Long, data: ByteArray) {
        var off = 0
        while (off < data.size) {  // a read never exceeds 4 KiB, but keep the length field honest
            val n = minOf(data.size - off, 0xFFFF)
            head.clear(); head.putLong(arrivalNs); head.putShort(n.toShort())
            out.write(head.array(), 0, 10)
            out.write(data, off, n)
            off += n
        }
        bytes += data.size
    }

    fun close() = out.close()
}

/**
 * Foreground service that owns the IMU link and records one phase of a session at a time (a
 * calibration position, a drift run, the placement check or the flight). Every Bluetooth read,
 * GNSS fix and file write happens on one background thread, so the screen can be off and the
 * app in the background. If Android kills the service it restarts and resumes the phase.
 *
 * Between phases the link stays up for a while, so the screens can show the IMU's orientation
 * and the calibration positions don't each wait for a reconnect.
 */
class RecorderService : Service(), ImuLink.Listener {
    private lateinit var thread: HandlerThread
    private lateinit var handler: Handler
    private var lm: LocationManager? = null
    private var wake: PowerManager.WakeLock? = null
    private lateinit var prefs: Prefs

    // the IMU
    private var link: ImuLink? = null
    private var linkKey = ""
    private var parser: WitParser? = null
    private var variant: Variant? = null
    private var imuConnected = false
    private var gyroInBlock = 0
    private var lastVolt: Double? = null
    private var lastTemp: Double? = null
    private val readback = HashMap<Int, Int>()
    private var configApplied = false

    // the phase being recorded
    private var session: Session? = null
    private var phase: String? = null
    private var startNs = 0L
    private var targetStillS = 0.0
    private var imuOut: ImuWriter? = null
    private var gnss: CsvGz? = null
    private var events: CsvGz? = null
    private var drops = 0

    private var block = BlockStats(0.06, 0.006)
    private var blockStartNs = 0L
    private var stillS = 0.0
    private var streak = 0.0
    private val gyroRing = ArrayDeque<DoubleArray>()  // 1-s gyro means over the last 5 min
    private var displayBias: DoubleArray? = null
    private val calSums = HashMap<String, DoubleArray>()  // per-position gyro sums for display bias
    private var refGravity: DoubleArray? = null
    private var refBlocks = 0
    private var shiftBlocks = 0
    private var lastFixNs = 0L
    private var lastVz = 0.0
    private var lastAlt = Double.NaN
    private val accum = HashMap<Transport.Model, Double>()
    private var transportAccum = 0.0
    private var sats = 0

    // reminders to turn the IMU
    private var nextTurnAtMs = 0L
    private var turnAlerted = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        prefs = Prefs(this)
        thread = HandlerThread("lll-recorder").apply { start() }
        handler = Handler(thread.looper)
        lm = getSystemService(LocationManager::class.java)
        handler.post(batteryTick)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            null -> {  // restarted by the system after being killed
                val sid = prefs.activeSession
                val ph = prefs.activePhase
                if (sid != null && ph != null) {
                    goForeground("Resuming $ph")
                    handler.post { startPhase(sid, ph, prefs.activeTargetStillS.toDouble(), resume = true) }
                } else stopSelf()
            }
            ACTION_MONITOR -> { goForeground("Connected to the IMU"); handler.post { ensureLink(); scheduleIdleStop() } }
            ACTION_CONFIGURE -> { goForeground("Configuring the IMU"); handler.post { ensureLink(); configApplied = false; applyConfig(); scheduleIdleStop() } }
            ACTION_DISCONNECT -> handler.post { if (phase == null) shutdown() }
            ACTION_START -> {
                goForeground("Recording: ${intent.getStringExtra(EXTRA_PHASE) ?: ""}")
                val sid = intent.getStringExtra(EXTRA_SESSION) ?: return START_STICKY
                val ph = intent.getStringExtra(EXTRA_PHASE) ?: return START_STICKY
                val target = intent.getDoubleExtra(EXTRA_TARGET_STILL_S, 0.0)
                handler.post { startPhase(sid, ph, target) }
            }
            ACTION_STOP -> handler.post { stopPhase() }
            ACTION_EVENT -> {
                val kind = intent.getStringExtra(EXTRA_KIND) ?: "note"
                val detail = intent.getStringExtra(EXTRA_DETAIL) ?: ""
                handler.post { event(kind, detail); if (kind == "placement_shift") markShift("Placement shift logged") }
            }
            ACTION_TURN_DONE -> {
                val how = intent.getStringExtra(EXTRA_DETAIL) ?: "plane180"
                handler.post { turnDone(how) }
            }
        }
        return START_STICKY
    }

    private fun hasPerm(p: String) = ContextCompat.checkSelfPermission(this, p) == PackageManager.PERMISSION_GRANTED
    private fun canConnect() = Build.VERSION.SDK_INT < 31 || hasPerm(Manifest.permission.BLUETOOTH_CONNECT)

    private fun notification(text: String): Notification {
        val pi = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        return NotificationCompat.Builder(this, LllApp.CHANNEL)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setContentIntent(pi)
            .build()
    }

    private fun goForeground(text: String) {
        val n = notification(text)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            var type = 0
            if (canConnect()) type = type or ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE
            if (hasPerm(Manifest.permission.ACCESS_FINE_LOCATION)) type = type or ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION
            if (type != 0) startForeground(NOTIF_ID, n, type) else startForeground(NOTIF_ID, n)
        } else startForeground(NOTIF_ID, n)
    }

    private fun updateNotification(text: String) =
        getSystemService(NotificationManager::class.java).notify(NOTIF_ID, notification(text))

    // ---- the IMU link ----

    private fun ensureLink() {
        val v = prefs.imuVariant
        val addr = prefs.imuAddress
        if (v == null || addr.isEmpty()) { fail("No IMU chosen. Pick one in Settings."); return }
        if (!canConnect()) { fail("Bluetooth permission is missing. Grant it in Settings."); return }
        val key = "${v.key}@$addr"
        if (link != null && key == linkKey) return
        link?.close()
        variant = v; linkKey = key
        parser = WitParser(v)
        imuConnected = false
        readback.clear(); configApplied = false
        Live.state.update { it.copy(imuStatus = "connecting…", imuConnected = false, imuConfigOk = null) }
        Live.activity("Connecting to ${prefs.imuName.ifEmpty { "the IMU" }}")
        link = ImuLink.create(this, v, addr, this).also { it.open() }
    }

    override fun onBytes(arrivalNs: Long, data: ByteArray) {
        handler.post { onImuBytes(arrivalNs, data) }
    }

    override fun onState(connected: Boolean, detail: String) {
        handler.post {
            if (connected == imuConnected) return@post
            imuConnected = connected
            Live.state.update { it.copy(imuConnected = connected, imuStatus = if (connected) "connected" else "reconnecting: $detail") }
            if (connected) {
                Live.activity("IMU connected")
                if (phase != null) event("imu_connect", detail)
                cancelAlert(ALERT_LINK)
                checkConfig()
            } else {
                Live.activity("IMU link lost ($detail); reconnecting")
                if (phase != null) {
                    event("imu_disconnect", detail)
                    drops++
                    alert(ALERT_LINK, "IMU link lost", "Reconnecting automatically. Keep the IMU powered and within a few metres.", withActions = false)
                }
            }
        }
    }

    private val sink = object : WitParser.Sink {
        override fun gyro(x: Double, y: Double, z: Double) { block.gyro(x, y, z); gyroInBlock++ }
        override fun accel(x: Double, y: Double, z: Double) = block.accel(x, y, z)
        override fun tempC(t: Double) { lastTemp = t }
        override fun volt(v: Double) { lastVolt = v }
        override fun registers(start: Int, values: IntArray) {
            for ((i, v) in values.withIndex()) readback[start + i] = v and 0xFFFF
        }
    }

    private fun onImuBytes(t: Long, data: ByteArray) {
        imuOut?.record(t, data)
        parser?.feed(data, sink = sink)
        if (blockStartNs == 0L) blockStartNs = t
        if (t - blockStartNs >= 1_000_000_000L) {
            val rate = gyroInBlock / ((t - blockStartNs) / 1e9)
            blockStartNs = t; gyroInBlock = 0
            Live.state.update { it.copy(imuRateHz = rate) }
            onBlock(block.close())
        }
    }

    /** Read the config registers back. If anything differs (for example after the IMU was
     *  power-cycled), write the config, save it, and check once more. */
    private fun checkConfig() {
        val v = variant ?: return
        val expected = WitConfig.expected(v, prefs.imuRateHz)
        readback.clear()
        expected.keys.forEachIndexed { i, reg ->
            handler.postDelayed({
                parser?.lastReadRegister = reg
                link?.write(listOf(WitConfig.read(reg)))
            }, 300L * i + 500)
        }
        handler.postDelayed({
            val got = expected.keys.associateWith { readback[it] }
            val ok = got.all { (reg, value) -> value == expected[reg] }
            val detail = got.entries.joinToString(" ") { (r, value) -> "0x%02x=%s".format(r, value?.let { "0x%x".format(it) } ?: "?") }
            Live.state.update { it.copy(imuConfigOk = ok) }
            if (phase != null) event("imu_config", "$detail ok=$ok")
            if (ok) Live.activity("IMU settings verified")
            else if (!configApplied) { Live.activity("IMU settings differ ($detail); writing them"); applyConfig() }
            else Live.activity("IMU settings still differ after writing ($detail)")
        }, 300L * expected.size + 1500)
    }

    private fun applyConfig() {
        val v = variant ?: return
        if (!imuConnected) return  // checkConfig runs again on connect
        configApplied = true
        val cmds = WitConfig.apply(v, prefs.imuRateHz)
        link?.write(cmds)
        if (phase != null) event("imu_config_write", "rate=${prefs.imuRateHz}")
        handler.postDelayed({ checkConfig() }, 150L * cmds.size + 1500)
    }

    // ---- phases ----

    @SuppressLint("MissingPermission")
    private fun startPhase(sessionId: String, ph: String, target: Double, resume: Boolean = false) {
        if (phase != null) closePhase()
        handler.removeCallbacks(idleStop)
        val s = SessionStore.load(this, sessionId) ?: run { fail("session not found"); return }
        session = s; phase = ph; targetStillS = target
        startNs = if (resume) prefs.activeStartNs else SystemClock.elapsedRealtimeNanos()
        if (!resume) { prefs.activeSession = sessionId; prefs.activePhase = ph; prefs.activeStartNs = startNs; prefs.activeTargetStillS = target.toFloat() }
        stillS = 0.0; streak = 0.0; refGravity = null; refBlocks = 0; shiftBlocks = 0; drops = 0
        accum.clear(); transportAccum = 0.0; lastFixNs = 0L; gyroRing.clear(); lastAlt = Double.NaN
        displayBias = s.local.optJSONArray("display_bias")?.let { a -> DoubleArray(3) { a.getDouble(it) } }
        val inAircraft = ph == "flight" || ph == "placement_check"
        block = if (inAircraft) BlockStats(0.25, 0.03) else BlockStats(0.06, 0.006)
        blockStartNs = 0L; gyroInBlock = 0

        wake = wake ?: getSystemService(PowerManager::class.java).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "lll:recording").apply {
            setReferenceCounted(false); acquire(24 * 3600 * 1000L)
        }
        events = CsvGz(File(s.dir, "events.csv.gz"), "t_ns,kind,detail")
        event(if (resume) "phase_resume" else "phase_start", ph)
        imuOut = ImuWriter(File(s.dir, "imu.bin.gz"))
        ensureLink()
        if (imuConnected) { event("imu_connect", "already connected"); checkConfig() }
        val unit = prefs.unitId(prefs.imuAddress)
        if (s.manifest.optJSONObject("imu")?.optString("unit_id") != unit) SessionStore.addFlag(s, "imu_changed_mid_session")

        if (inAircraft && hasPerm(Manifest.permission.ACCESS_FINE_LOCATION)) {
            gnss = CsvGz(File(s.dir, "gnss.csv.gz"),
                "t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used")
            lm?.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, locListener, thread.looper)
            lm?.registerGnssStatusCallback(gnssCb, handler)
        }
        if (ph.startsWith("cal_") && hasPerm(Manifest.permission.ACCESS_FINE_LOCATION) && prefs.shareCalLatitude &&
            s.manifest.getJSONObject("privacy").isNull("cal_lat_deg")) {
            val last = listOf(LocationManager.PASSIVE_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER)
                .mapNotNull { runCatching { lm?.getLastKnownLocation(it) }.getOrNull() }.maxByOrNull { it.time }
            if (last != null) s.manifest.getJSONObject("privacy").put("cal_lat_deg", floor(last.latitude * 2 + 0.5) / 2)
        }
        // reminders to turn the IMU, during the flight only
        val every = prefs.indexAlertMinutes
        nextTurnAtMs = if (ph == "flight" && every > 0) SystemClock.elapsedRealtime() + every * 60_000L else 0L
        turnAlerted = false
        s.save()
        Live.activity(if (resume) "Resumed recording $ph after a restart" else "Started recording $ph")
        handler.removeCallbacks(uiTick); handler.post(uiTick)
        publish()
    }

    private fun stopPhase() {
        val ph = phase
        closePhase()
        if (ph != null) Live.activity("Stopped recording $ph")
        updateNotification("Connected to the IMU (not recording)")
        scheduleIdleStop()
    }

    /** End the current phase and record it in the manifest. The link stays up. */
    private fun closePhase() {
        val s = session ?: return
        val ph = phase ?: return
        lm?.removeUpdates(locListener)
        lm?.unregisterGnssStatusCallback(gnssCb)
        handler.removeCallbacks(uiTick)
        val endNs = SystemClock.elapsedRealtimeNanos()
        event("phase_stop", "$ph still_s=${"%.1f".format(stillS)} link_drops=$drops")
        imuOut?.close(); gnss?.close(); events?.close()
        imuOut = null; gnss = null; events = null
        SessionStore.addPhase(s, ph, startNs, endNs, stillS)
        prefs.activeSession = null; prefs.activePhase = null
        // display-only bias estimate once the four pre-flight positions are done
        val acc = calSums[ph]
        if (ph.startsWith("cal_pre.") && acc != null && acc[3] > 0) {
            val cm = s.local.optJSONObject("cal_means") ?: JSONObject().also { s.local.put("cal_means", it) }
            cm.put(ph, JSONArray(listOf(acc[0] / acc[3], acc[1] / acc[3], acc[2] / acc[3])))
            // average each position's visits, then the four positions: the Earth's rotation cancels
            val byPos = cm.keys().asSequence().toList().groupBy { it.split(".")[1] }
            if (byPos.size == 4) {
                val pos = byPos.values.map { keys -> DoubleArray(3) { i -> keys.sumOf { cm.getJSONArray(it).getDouble(i) } / keys.size } }
                s.local.put("display_bias", JSONArray(List(3) { i -> pos.sumOf { it[i] } / 4 }))
            }
            s.save()
        }
        calSums.clear()
        nextTurnAtMs = 0L
        cancelAlert(ALERT_TURN); cancelAlert(ALERT_LINK)
        val done = ph
        session = null; phase = null
        wake?.let { if (it.isHeld) it.release() }
        wake = null
        Live.state.update { it.copy(lastCompletedPhase = done, phase = null, sessionId = null, turnDue = false, nextTurnInS = null) }
    }

    private val idleStop = Runnable { if (phase == null) shutdown() }

    /** Keep the link up for 10 minutes between phases, then let go of it. */
    private fun scheduleIdleStop() {
        handler.removeCallbacks(idleStop)
        handler.postDelayed(idleStop, 10 * 60_000L)
    }

    private fun shutdown() {
        handler.removeCallbacks(idleStop)
        link?.close(); link = null; linkKey = ""; imuConnected = false
        Live.state.update { it.copy(imuConnected = false, imuStatus = "not connected") }
        wake?.let { if (it.isHeld) it.release() }
        wake = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        if (phase != null) handler.post { closePhase() }
        handler.post { link?.close(); link = null }
        thread.quitSafely()
        super.onDestroy()
    }

    private fun fail(msg: String) {
        Live.state.update { it.copy(error = msg, imuStatus = msg) }
        Live.activity(msg)
        if (phase == null) shutdown()
    }

    private fun event(kind: String, detail: String) {
        events?.row(SystemClock.elapsedRealtimeNanos(), kind, detail.replace(Regex("[,\\r\\n]"), " "))
    }

    private fun markShift(msg: String) {
        session?.let { SessionStore.addFlag(it, "placement_shift") }
        refGravity = null; refBlocks = 0
        Live.activity(msg)
    }

    // ---- turn reminders ----

    private fun turnDone(how: String) {
        if (phase == null) return
        if (how == "skip") { event("index_skip", ""); Live.activity("Turn reminder skipped") }
        else { event("index_turn", how); markShift(if (how == "flip") "IMU flipped upside down" else "IMU turned 180° in its plane") }
        turnAlerted = false
        val every = prefs.indexAlertMinutes
        nextTurnAtMs = if (every > 0) SystemClock.elapsedRealtime() + every * 60_000L else 0L
        cancelAlert(ALERT_TURN)
        publish()
    }

    private fun alert(id: Int, title: String, text: String, withActions: Boolean) {
        val motions = prefs.turnMotions
        val pi = PendingIntent.getActivity(this, id, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val b = NotificationCompat.Builder(this, LllApp.ALERTS)
            .setContentTitle(title).setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setSmallIcon(android.R.drawable.ic_popup_reminder)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setContentIntent(pi)
            .setAutoCancel(false)
        if (withActions) {
            fun act(req: Int, label: String, how: String) = b.addAction(0, label, PendingIntent.getService(this, req,
                Intent(this, RecorderService::class.java).setAction(ACTION_TURN_DONE).putExtra(EXTRA_DETAIL, how),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT))
            if (motions != "flip") act(10, "Turned 180°", "plane180")
            if (motions != "plane180") act(11, "Flipped over", "flip")
            act(12, "Skip", "skip")
        }
        if (Build.VERSION.SDK_INT < 33 || hasPerm(Manifest.permission.POST_NOTIFICATIONS)) {
            getSystemService(NotificationManager::class.java).notify(id, b.build())
        }
    }

    private fun cancelAlert(id: Int) = getSystemService(NotificationManager::class.java).cancel(id)

    // ---- stillness, placement ----

    private fun onBlock(still: Boolean) {
        val ph = phase
        val g = block.lastGyroMean
        if (ph == null) { publishPreview(); return }
        if (still) { stillS += 1.0; streak += 1.0 } else streak = 0.0
        if (ph.startsWith("cal_pre.") && still) {
            val acc = calSums.getOrPut(ph) { DoubleArray(4) }
            acc[0] += g[0]; acc[1] += g[1]; acc[2] += g[2]; acc[3] += 1.0
        }
        gyroRing.addLast(g)
        while (gyroRing.size > 300) gyroRing.removeFirst()
        // A placement shift in cruise: the tilt moves more than 2° from the cruise reference
        if (ph == "flight") {
            val inCruise = lastFixNs != 0L && Live.state.value.speedMps > 100 && kotlin.math.abs(lastVz) < 2.0
            if (inCruise && refGravity == null && refBlocks++ >= 60) refGravity = block.lastAccelMean.copyOf()
            val ref = refGravity
            if (inCruise && ref != null) {
                if (BlockStats.angleDeg(ref, block.lastAccelMean) > 2.0) shiftBlocks++ else shiftBlocks = 0
                if (shiftBlocks == 60) { event("placement_shift", "auto tilt>2deg"); markShift("The IMU's tilt changed by more than 2°") }
            }
        }
        if (targetStillS > 0 && stillS >= targetStillS) stopPhase()
    }

    // ---- GNSS ----

    private val locListener = object : LocationListener {
        override fun onLocationChanged(l: Location) = onFix(l)
        @Deprecated("Deprecated in Java") override fun onStatusChanged(p: String?, s: Int, b: Bundle?) {}
        override fun onProviderEnabled(p: String) = event("gnss_provider", "enabled")
        override fun onProviderDisabled(p: String) = event("gnss_provider", "disabled")
    }

    private val gnssCb = object : GnssStatus.Callback() {
        override fun onSatelliteStatusChanged(status: GnssStatus) {
            sats = (0 until status.satelliteCount).count { status.usedInFix(it) }
        }
    }

    private fun onFix(l: Location) {
        val w = gnss ?: return
        fun f(has: Boolean, v: Float) = if (has) v.toString() else ""
        w.row(
            l.elapsedRealtimeNanos, l.time.toString(), l.latitude.toString(), l.longitude.toString(),
            if (l.hasAltitude()) l.altitude.toString() else "",
            f(l.hasSpeed(), l.speed), f(l.hasBearing(), l.bearing), f(l.hasAccuracy(), l.accuracy),
            f(l.hasVerticalAccuracy(), l.verticalAccuracyMeters), f(l.hasSpeedAccuracy(), l.speedAccuracyMetersPerSecond),
            f(l.hasBearingAccuracy(), l.bearingAccuracyDegrees), sats.toString(),
        )
        if (lastFixNs == 0L) Live.activity("GPS fix: $sats satellites")
        // display-only predictions, accumulated over the flight
        val lat = Math.toRadians(l.latitude)
        val psi = Math.toRadians(l.bearing.toDouble())
        val v = l.speed.toDouble()
        val vN = v * cos(psi); val vE = v * sin(psi)
        val dt = if (lastFixNs == 0L) 0.0 else ((l.elapsedRealtimeNanos - lastFixNs) / 1e9).coerceAtMost(5.0)
        if (!lastAlt.isNaN() && dt > 0) lastVz = 0.9 * lastVz + 0.1 * ((l.altitude - lastAlt) / dt)
        lastAlt = l.altitude
        lastFixNs = l.elapsedRealtimeNanos
        for (m in Transport.Model.entries) {
            val p = Transport.norm(Transport.predict(m, lat, l.altitude, vN, vE))
            accum[m] = (accum[m] ?: 0.0) + Math.toDegrees(p * dt)
        }
        transportAccum += Math.toDegrees(Transport.norm(Transport.transportRate(lat, l.altitude, vN, vE)) * dt)
        Live.state.update {
            it.copy(
                hasFix = true, speedMps = v, altM = l.altitude, bearingDeg = l.bearing.toDouble(), latDeg = l.latitude,
                sats = sats, hAccM = l.accuracy.toDouble(),
                predictedDph = Transport.Model.entries.associateWith { m ->
                    Transport.norm(Transport.predict(m, lat, l.altitude, vN, vE)) * Transport.RAD_TO_DEG_PER_HOUR
                },
                transportDph = Transport.norm(Transport.transportRate(lat, l.altitude, vN, vE)) * Transport.RAD_TO_DEG_PER_HOUR,
                accumulatedDeg = accum.toMap(), transportAccumDeg = transportAccum,
            )
        }
    }

    // ---- periodic ----

    private val batteryTick = object : Runnable {
        override fun run() {
            val i = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            if (i != null) {
                val pct = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) * 100 / maxOf(1, i.getIntExtra(BatteryManager.EXTRA_SCALE, 100))
                val plugged = i.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) != 0
                Live.state.update { it.copy(phoneBatteryPct = pct.takeIf { p -> p >= 0 }, phoneCharging = plugged) }
            }
            handler.postDelayed(this, 30_000)
        }
    }

    private var uiTicks = 0

    private val uiTick = object : Runnable {
        override fun run() {
            publish()
            if (nextTurnAtMs > 0 && !turnAlerted && SystemClock.elapsedRealtime() >= nextTurnAtMs) {
                turnAlerted = true
                Live.activity("Time to turn the IMU")
                alert(ALERT_TURN, "Time to turn the IMU", turnInstruction(prefs.turnMotions), withActions = true)
            }
            if (++uiTicks % 10 == 0) phase?.let { ph ->
                val st = Live.state.value
                updateNotification("Recording $ph · ${fmtElapsed(st.elapsedS)} · IMU ${if (imuConnected) "%.0f Hz".format(st.imuRateHz) else "reconnecting"}" +
                    if (st.hasFix) " · GPS ${st.sats} sats" else "")
            }
            handler.postDelayed(this, 1000)
        }
    }

    private fun turnInstruction(motions: String) = when (motions) {
        "plane180" -> "Turn it to face the opposite way, keeping the same side up. Fix it firmly again, then tap Turned 180°."
        "flip" -> "Flip it upside down in its mount. Fix it firmly again, then tap Flipped over."
        else -> "Turn it to face the opposite way with the same side up (best), or turn it upside down. Fix it firmly again, then tap what you did."
    }

    private fun fmtElapsed(s: Double): String { val t = s.toLong(); return "%d:%02d:%02d".format(t / 3600, t / 60 % 60, t % 60) }

    private fun gravityAxis(gm: DoubleArray) = listOf("x", "y", "z").zip(gm.toList()).maxByOrNull { kotlin.math.abs(it.second) }
        ?.let { (if (it.second >= 0) "+" else "-") + it.first } ?: ""

    /** Between phases: orientation and noise only, for the calibration and placement screens. */
    private fun publishPreview() {
        val gm = block.lastAccelMean
        Live.state.update {
            it.copy(gravityAxis = gravityAxis(gm), gravity = FloatArray(3) { i -> gm[i].toFloat() },
                accelSd = block.lastAccelSd, gyroSdDps = Math.toDegrees(block.lastGyroSd),
                imuVolt = lastVolt, imuTempC = lastTemp, imuBadChecksums = parser?.badChecksums ?: 0)
        }
    }

    private fun publish() {
        val ph = phase ?: return
        val gm = block.lastAccelMean
        val bias = displayBias
        val measured = if (bias != null && gyroRing.size >= 60) {
            val mean = DoubleArray(3) { i -> gyroRing.sumOf { it[i] } / gyroRing.size - bias[i] }
            Transport.norm(mean) * Transport.RAD_TO_DEG_PER_HOUR
        } else null
        val turnIn = if (nextTurnAtMs > 0) (nextTurnAtMs - SystemClock.elapsedRealtime()) / 1000.0 else null
        Live.state.update {
            it.copy(
                sessionId = session?.id, phase = ph,
                elapsedS = (SystemClock.elapsedRealtimeNanos() - startNs) / 1e9,
                stillS = stillS, stillStreakS = streak, isStill = streak > 0, targetStillS = targetStillS,
                gravityAxis = gravityAxis(gm), gravity = FloatArray(3) { i -> gm[i].toFloat() },
                tiltShiftDeg = refGravity?.let { r -> BlockStats.angleDeg(r, gm) } ?: 0.0,
                accelSd = block.lastAccelSd, gyroSdDps = Math.toDegrees(block.lastGyroSd),
                imuBytes = imuOut?.bytes ?: 0, imuBadChecksums = parser?.badChecksums ?: 0, imuDrops = drops,
                imuVolt = lastVolt, imuTempC = lastTemp,
                measuredDph = measured, nextTurnInS = turnIn, turnDue = turnAlerted,
                shiftWarning = session?.manifest?.getJSONObject("quality")?.getJSONArray("flags")?.toString()?.contains("placement_shift") == true,
                error = null,
            )
        }
    }

    companion object {
        const val ACTION_START = "start"
        const val ACTION_STOP = "stop"
        const val ACTION_EVENT = "event"
        const val ACTION_MONITOR = "monitor"
        const val ACTION_CONFIGURE = "configure"
        const val ACTION_DISCONNECT = "disconnect"
        const val ACTION_TURN_DONE = "turn_done"
        const val EXTRA_SESSION = "session"
        const val EXTRA_PHASE = "phase"
        const val EXTRA_TARGET_STILL_S = "target_still_s"
        const val EXTRA_KIND = "kind"
        const val EXTRA_DETAIL = "detail"
        private const val NOTIF_ID = 1
        private const val ALERT_TURN = 2
        private const val ALERT_LINK = 3

        fun start(ctx: Context, sessionId: String, phase: String, targetStillS: Double = 0.0) {
            ContextCompat.startForegroundService(ctx, Intent(ctx, RecorderService::class.java).setAction(ACTION_START)
                .putExtra(EXTRA_SESSION, sessionId).putExtra(EXTRA_PHASE, phase).putExtra(EXTRA_TARGET_STILL_S, targetStillS))
        }

        fun stop(ctx: Context) {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_STOP))
        }

        /** Connect to the IMU without recording, for orientation previews. */
        fun monitor(ctx: Context) {
            ContextCompat.startForegroundService(ctx, Intent(ctx, RecorderService::class.java).setAction(ACTION_MONITOR))
        }

        fun configure(ctx: Context) {
            ContextCompat.startForegroundService(ctx, Intent(ctx, RecorderService::class.java).setAction(ACTION_CONFIGURE))
        }

        fun disconnect(ctx: Context) {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_DISCONNECT))
        }

        fun event(ctx: Context, kind: String, detail: String = "") {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_EVENT)
                .putExtra(EXTRA_KIND, kind).putExtra(EXTRA_DETAIL, detail))
        }

        fun turnDone(ctx: Context, how: String) {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_TURN_DONE).putExtra(EXTRA_DETAIL, how))
        }
    }
}

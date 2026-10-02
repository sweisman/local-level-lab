// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording

import android.Manifest
import android.annotation.SuppressLint
import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
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
import io.github.sweisman.locallevellab.ui.MainActivity
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedWriter
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStreamWriter
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
 * Foreground service that records one phase of a session (one calibration position, a drift run,
 * the placement check, or the flight). Every sensor callback, GNSS fix and file write happens on
 * one background thread.
 */
class RecorderService : Service(), SensorEventListener {
    private lateinit var thread: HandlerThread
    private lateinit var handler: Handler
    private lateinit var sm: SensorManager
    private var lm: LocationManager? = null
    private var wake: PowerManager.WakeLock? = null

    private var session: Session? = null
    private var phase: String? = null
    private var startNs = 0L
    private var targetStillS = 0.0
    private val writers = HashMap<String, CsvGz>()
    private val streamOf = HashMap<Int, String>()
    private var events: CsvGz? = null

    private lateinit var block: BlockStats
    private var blockStartNs = 0L
    private var stillS = 0.0
    private var streak = 0.0
    private val gyroRing = ArrayDeque<DoubleArray>()  // 1-s gyro means over the last 5 min
    private var displayBias: DoubleArray? = null
    private var calSums = HashMap<String, DoubleArray>()  // per-position gyro sums for display bias
    private var refGravity: DoubleArray? = null
    private var refBlocks = 0
    private var shiftBlocks = 0
    private var lastFixNs = 0L
    private var lastVz = 0.0
    private var lastAlt = Double.NaN
    private val accum = HashMap<Transport.Model, Double>()
    private var transportAccum = 0.0
    private var sats = 0

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        thread = HandlerThread("lll-recorder").apply { start() }
        handler = Handler(thread.looper)
        sm = getSystemService(SensorManager::class.java)
        lm = getSystemService(LocationManager::class.java)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                goForeground(intent.getStringExtra(EXTRA_PHASE) ?: "")
                val sid = intent.getStringExtra(EXTRA_SESSION) ?: return START_NOT_STICKY
                val ph = intent.getStringExtra(EXTRA_PHASE) ?: return START_NOT_STICKY
                val target = intent.getDoubleExtra(EXTRA_TARGET_STILL_S, 0.0)
                handler.post { startPhase(sid, ph, target) }
            }
            ACTION_STOP -> handler.post { stopPhase() }
            ACTION_EVENT -> {
                val kind = intent.getStringExtra(EXTRA_KIND) ?: "note"
                val detail = intent.getStringExtra(EXTRA_DETAIL) ?: ""
                handler.post { event(kind, detail); if (kind == "placement_shift") markShift() }
            }
        }
        return START_NOT_STICKY
    }

    private fun goForeground(phase: String) {
        val pi = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val n: Notification = NotificationCompat.Builder(this, LllApp.CHANNEL)
            .setContentTitle(getString(R.string.app_name))
            .setContentText("Recording: $phase")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .setContentIntent(pi)
            .build()
        val hasLoc = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && hasLoc) {
            startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        } else {
            startForeground(NOTIF_ID, n)
        }
    }

    @SuppressLint("MissingPermission")
    private fun startPhase(sessionId: String, ph: String, target: Double) {
        if (phase != null) closePhase()
        val s = SessionStore.load(this, sessionId) ?: run { fail("session not found"); return }
        session = s; phase = ph; targetStillS = target
        startNs = SystemClock.elapsedRealtimeNanos()
        stillS = 0.0; streak = 0.0; refGravity = null; refBlocks = 0; shiftBlocks = 0
        accum.clear(); transportAccum = 0.0; lastFixNs = 0L; gyroRing.clear(); lastAlt = Double.NaN
        displayBias = s.local.optJSONArray("display_bias")?.let { a -> DoubleArray(3) { a.getDouble(it) } }
        val inAircraft = ph == "flight" || ph == "placement_check"
        block = if (inAircraft) BlockStats(0.25, 0.03) else BlockStats(0.06, 0.006)
        blockStartNs = 0L

        wake = wake ?: getSystemService(PowerManager::class.java).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "lll:recording").apply {
            setReferenceCounted(false); acquire(24 * 3600 * 1000L)
        }
        events = CsvGz(File(s.dir, "events.csv.gz"), "t_ns,kind,detail")
        event("phase_start", ph)

        val sensorsJson = s.manifest.getJSONObject("sensors")
        for ((name, type, header) in STREAMS) {
            val sensor = sm.getDefaultSensor(type) ?: continue
            writers[name] = CsvGz(File(s.dir, "$name.csv.gz"), header)
            streamOf[type] = name
            sensorsJson.put(name, JSONObject()
                .put("name", sensor.name).put("vendor", sensor.vendor).put("version", sensor.version)
                .put("resolution", sensor.resolution.toDouble()).put("max_range", sensor.maximumRange.toDouble())
                .put("min_delay_us", sensor.minDelay).put("fifo_max", sensor.fifoMaxEventCount))
            sm.registerListener(this, sensor, Recorder.SAMPLING_PERIOD_US, 200_000, handler)
        }
        if (!writers.containsKey("gyro_uncal")) SessionStore.addFlag(s, "no_uncalibrated_gyro")

        val hasLoc = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (inAircraft && hasLoc) {
            writers["gnss"] = CsvGz(File(s.dir, "gnss.csv.gz"),
                "t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used")
            lm?.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, locListener, thread.looper)
            lm?.registerGnssStatusCallback(gnssCb, handler)
        }
        if (ph.startsWith("cal_") && hasLoc && Prefs(this).shareCalLatitude && s.manifest.getJSONObject("privacy").isNull("cal_lat_deg")) {
            val last = listOf(LocationManager.PASSIVE_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER)
                .mapNotNull { runCatching { lm?.getLastKnownLocation(it) }.getOrNull() }.maxByOrNull { it.time }
            if (last != null) s.manifest.getJSONObject("privacy").put("cal_lat_deg", floor(last.latitude * 2 + 0.5) / 2)
        }
        writers["battery"] = CsvGz(File(s.dir, "battery.csv.gz"), "t_ns,temp_c,level_pct,plugged")
        handler.post(batteryTick)
        handler.post(uiTick)
        s.save()
        publish()
    }

    private fun stopPhase() {
        closePhase()
        shutdown()
    }

    /** End the current phase and record it in the manifest, keeping the service alive. */
    private fun closePhase() {
        val s = session ?: return
        val ph = phase ?: return
        sm.unregisterListener(this)
        lm?.removeUpdates(locListener)
        lm?.unregisterGnssStatusCallback(gnssCb)
        handler.removeCallbacks(batteryTick)
        handler.removeCallbacks(uiTick)
        val endNs = SystemClock.elapsedRealtimeNanos()
        event("phase_stop", "$ph still_s=${"%.1f".format(stillS)}")
        writers.values.forEach { it.close() }
        events?.close()
        writers.clear(); streamOf.clear(); events = null
        SessionStore.addPhase(s, ph, startNs, endNs, stillS)
        // display-only bias estimate once the four pre-flight positions are done
        val acc = calSums[ph]
        if (ph.startsWith("cal_pre.") && acc != null && acc[3] > 0) {
            val cm = s.local.optJSONObject("cal_means") ?: JSONObject().also { s.local.put("cal_means", it) }
            cm.put(ph, JSONArray(listOf(acc[0] / acc[3], acc[1] / acc[3], acc[2] / acc[3])))
            if (cm.length() == 4) {
                val means = cm.keys().asSequence().map { k -> cm.getJSONArray(k) }.toList()
                s.local.put("display_bias", JSONArray(List(3) { i -> means.sumOf { it.getDouble(i) } / 4 }))
            }
            s.save()
        }
        calSums.clear()
        val done = ph
        session = null; phase = null
        Live.state.value = LiveState(lastCompletedPhase = done)
    }

    private fun shutdown() {
        wake?.let { if (it.isHeld) it.release() }
        wake = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        if (phase != null) handler.post { stopPhase() }
        thread.quitSafely()
        super.onDestroy()
    }

    private fun fail(msg: String) {
        Live.state.value = LiveState(error = msg)
        shutdown()
    }

    private fun event(kind: String, detail: String) {
        events?.row(SystemClock.elapsedRealtimeNanos(), kind, detail.replace(Regex("[,\\r\\n]"), " "))
    }

    private fun markShift() {
        session?.let { SessionStore.addFlag(it, "placement_shift") }
        refGravity = null; refBlocks = 0
    }

    // ---- sensors (on the recorder thread) ----

    override fun onSensorChanged(e: SensorEvent) {
        val name = streamOf[e.sensor.type] ?: return
        val w = writers[name] ?: return
        val v = e.values
        when (name) {
            "pressure" -> w.row(e.timestamp, v[0].toString())
            "game_rv" -> w.row(e.timestamp, v[0].toString(), v[1].toString(), v[2].toString(), if (v.size > 3) v[3].toString() else "")
            "gyro", "accel" -> w.row(e.timestamp, v[0].toString(), v[1].toString(), v[2].toString())
            else -> w.row(e.timestamp, v[0].toString(), v[1].toString(), v[2].toString(), v[3].toString(), v[4].toString(), v[5].toString())
        }
        // stats for the live display and the stillness gate (never written)
        if (name == "accel_uncal" || (name == "accel" && !writers.containsKey("accel_uncal"))) block.accel(v[0], v[1], v[2])
        if (name == "gyro_uncal" || (name == "gyro" && !writers.containsKey("gyro_uncal"))) block.gyro(v[0], v[1], v[2])
        if (blockStartNs == 0L) blockStartNs = e.timestamp
        if (e.timestamp - blockStartNs >= 1_000_000_000L) {
            blockStartNs = e.timestamp
            onBlock(block.close())
        }
    }

    override fun onAccuracyChanged(sensor: Sensor, accuracy: Int) {
        event("sensor_accuracy", "${streamOf[sensor.type] ?: sensor.type} $accuracy")
    }

    private fun onBlock(still: Boolean) {
        val ph = phase ?: return
        if (still) { stillS += 1.0; streak += 1.0 } else streak = 0.0
        val g = block.lastGyroMean
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
                if (shiftBlocks == 60) { event("placement_shift", "auto tilt>2deg"); markShift() }
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
        val w = writers["gnss"] ?: return
        fun f(has: Boolean, v: Float) = if (has) v.toString() else ""
        w.row(
            l.elapsedRealtimeNanos, l.time.toString(), l.latitude.toString(), l.longitude.toString(),
            if (l.hasAltitude()) l.altitude.toString() else "",
            f(l.hasSpeed(), l.speed), f(l.hasBearing(), l.bearing), f(l.hasAccuracy(), l.accuracy),
            f(l.hasVerticalAccuracy(), l.verticalAccuracyMeters), f(l.hasSpeedAccuracy(), l.speedAccuracyMetersPerSecond),
            f(l.hasBearingAccuracy(), l.bearingAccuracyDegrees), sats.toString(),
        )
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
        Live.state.value = Live.state.value.copy(
            hasFix = true, speedMps = v, altM = l.altitude, bearingDeg = l.bearing.toDouble(), latDeg = l.latitude,
            sats = sats, hAccM = l.accuracy.toDouble(),
            predictedDph = Transport.Model.entries.associateWith {
                Transport.norm(Transport.predict(it, lat, l.altitude, vN, vE)) * Transport.RAD_TO_DEG_PER_HOUR
            },
            transportDph = Transport.norm(Transport.transportRate(lat, l.altitude, vN, vE)) * Transport.RAD_TO_DEG_PER_HOUR,
            accumulatedDeg = accum.toMap(), transportAccumDeg = transportAccum,
        )
    }

    // ---- periodic ----

    private val batteryTick = object : Runnable {
        override fun run() {
            val i = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            if (i != null) {
                val temp = i.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Int.MIN_VALUE)
                val lvl = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) * 100f / i.getIntExtra(BatteryManager.EXTRA_SCALE, 100)
                writers["battery"]?.row(SystemClock.elapsedRealtimeNanos(),
                    if (temp == Int.MIN_VALUE) "" else (temp / 10f).toString(), lvl.toString(),
                    i.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0).toString())
            }
            handler.postDelayed(this, 10_000)
        }
    }

    private val uiTick = object : Runnable {
        override fun run() { publish(); handler.postDelayed(this, 1000) }
    }

    private fun publish() {
        val ph = phase ?: return
        val gm = block.lastAccelMean
        val axis = listOf("x", "y", "z").zip(gm.toList()).maxByOrNull { kotlin.math.abs(it.second) }
            ?.let { (if (it.second >= 0) "+" else "-") + it.first } ?: ""
        val bias = displayBias
        val measured = if (bias != null && gyroRing.size >= 60) {
            val mean = DoubleArray(3) { i -> gyroRing.sumOf { it[i] } / gyroRing.size - bias[i] }
            Transport.norm(mean) * Transport.RAD_TO_DEG_PER_HOUR
        } else null
        Live.state.value = Live.state.value.copy(
            sessionId = session?.id, phase = ph,
            elapsedS = (SystemClock.elapsedRealtimeNanos() - startNs) / 1e9,
            stillS = stillS, stillStreakS = streak, isStill = streak > 0, targetStillS = targetStillS,
            gravityAxis = axis, gravity = FloatArray(3) { gm[it].toFloat() },
            tiltShiftDeg = refGravity?.let { BlockStats.angleDeg(it, gm) } ?: 0.0,
            accelSd = block.lastAccelSd, gyroSdDps = Math.toDegrees(block.lastGyroSd),
            samples = writers.mapValues { it.value.rows }, measuredDph = measured,
            shiftWarning = session?.manifest?.getJSONObject("quality")?.getJSONArray("flags")?.toString()?.contains("placement_shift") == true,
            error = null,
        )
    }

    companion object {
        const val ACTION_START = "start"
        const val ACTION_STOP = "stop"
        const val ACTION_EVENT = "event"
        const val EXTRA_SESSION = "session"
        const val EXTRA_PHASE = "phase"
        const val EXTRA_TARGET_STILL_S = "target_still_s"
        const val EXTRA_KIND = "kind"
        const val EXTRA_DETAIL = "detail"
        private const val NOTIF_ID = 1

        private val STREAMS = listOf(
            Triple("gyro_uncal", Sensor.TYPE_GYROSCOPE_UNCALIBRATED, "t_ns,x,y,z,bx,by,bz"),
            Triple("gyro", Sensor.TYPE_GYROSCOPE, "t_ns,x,y,z"),
            Triple("accel_uncal", Sensor.TYPE_ACCELEROMETER_UNCALIBRATED, "t_ns,x,y,z,bx,by,bz"),
            Triple("accel", Sensor.TYPE_ACCELEROMETER, "t_ns,x,y,z"),
            Triple("mag_uncal", Sensor.TYPE_MAGNETIC_FIELD_UNCALIBRATED, "t_ns,x,y,z,bx,by,bz"),
            Triple("pressure", Sensor.TYPE_PRESSURE, "t_ns,hpa"),
            Triple("game_rv", Sensor.TYPE_GAME_ROTATION_VECTOR, "t_ns,x,y,z,w"),
        )

        fun start(ctx: Context, sessionId: String, phase: String, targetStillS: Double = 0.0) {
            ContextCompat.startForegroundService(ctx, Intent(ctx, RecorderService::class.java).setAction(ACTION_START)
                .putExtra(EXTRA_SESSION, sessionId).putExtra(EXTRA_PHASE, phase).putExtra(EXTRA_TARGET_STILL_S, targetStillS))
        }

        fun stop(ctx: Context) {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_STOP))
        }

        fun event(ctx: Context, kind: String, detail: String = "") {
            ctx.startService(Intent(ctx, RecorderService::class.java).setAction(ACTION_EVENT)
                .putExtra(EXTRA_KIND, kind).putExtra(EXTRA_DETAIL, detail))
        }
    }
}

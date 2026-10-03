// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.SharedPreferences
import io.github.sweisman.locallevellab.recording.imu.Variant
import java.util.UUID

class LllApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel(CHANNEL, getString(R.string.channel_recording), NotificationManager.IMPORTANCE_LOW))
        // Turn/flip reminders and link problems: sound and vibration, so they reach you with the screen off.
        nm.createNotificationChannel(NotificationChannel(ALERTS, "Reminders and alerts", NotificationManager.IMPORTANCE_HIGH).apply {
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 400, 200, 400)
        })
    }

    companion object {
        const val CHANNEL = "recording"
        const val ALERTS = "alerts"
    }
}

/** User settings. Everything stays on the device. */
class Prefs(ctx: Context) {
    private val p: SharedPreferences = ctx.getSharedPreferences("lll", Context.MODE_PRIVATE)

    /** A random ID per install. It links your own sessions together and nothing else. */
    val installId: String
        get() = p.getString("install_id", null) ?: UUID.randomUUID().toString().also {
            p.edit().putString("install_id", it).apply()
        }

    var consented: Boolean
        get() = p.getBoolean("consented", false)
        set(v) = p.edit().putBoolean("consented", v).apply()

    var serverUrl: String
        get() = p.getString("server_url", null) ?: BuildConfig.DEFAULT_SERVER_URL
        set(v) = p.edit().putString("server_url", v.trim().trimEnd('/')).apply()

    var unmeteredOnly: Boolean
        get() = p.getBoolean("unmetered_only", true)
        set(v) = p.edit().putBoolean("unmetered_only", v).apply()

    /** Store the calibration latitude rounded to 0.5° (needed for the ground Earth-rate test). */
    var shareCalLatitude: Boolean
        get() = p.getBoolean("share_cal_lat", true)
        set(v) = p.edit().putBoolean("share_cal_lat", v).apply()

    var calPositionMinutes: Int
        get() = p.getInt("cal_pos_min", 3)
        set(v) = p.edit().putInt("cal_pos_min", v.coerceIn(2, 15)).apply()

    var driftMinutes: Int
        get() = p.getInt("drift_min", 30)
        set(v) = p.edit().putInt("drift_min", v.coerceIn(10, 240)).apply()

    // ---- the IMU ----

    /** Bluetooth address of the chosen IMU. Stays on the phone; never written to a session. */
    var imuAddress: String
        get() = p.getString("imu_address", "") ?: ""
        set(v) = p.edit().putString("imu_address", v).apply()

    var imuName: String
        get() = p.getString("imu_name", "") ?: ""
        set(v) = p.edit().putString("imu_name", v).apply()

    var imuVariant: Variant?
        get() = Variant.of(p.getString("imu_variant", null))
        set(v) = p.edit().putString("imu_variant", v?.key).apply()

    var imuRateHz: Int
        get() = p.getInt("imu_rate_hz", 100)
        set(v) = p.edit().putInt("imu_rate_hz", v).apply()

    /** A random ID per physical IMU, so its bias can be modelled across sessions. It is
     *  derived from nothing; the phone keeps the address-to-ID mapping to itself. */
    fun unitId(address: String): String = p.getString("unit_$address", null)
        ?: UUID.randomUUID().toString().also { p.edit().putString("unit_$address", it).apply() }

    /** Which turns to ask for: "plane180" (face the opposite way, same side up), "flip" (upside
     *  down) or "both". Same-side-up turns are the useful ones: gravity stays on the same sensor
     *  axis, so the gyro's gravity-dependent error stays put while the signal moves. */
    var turnMotions: String
        get() = p.getString("turn_motions", "plane180") ?: "plane180"
        set(v) = p.edit().putString("turn_motions", v).apply()

    /** Minutes between "turn the IMU" reminders during long recordings; 0 = off. */
    var indexAlertMinutes: Int
        get() = p.getInt("index_alert_min", 60)
        set(v) = p.edit().putInt("index_alert_min", v.coerceIn(0, 240)).apply()

    // ---- the phase being recorded, so a restarted service can resume it ----

    var activeSession: String?
        get() = p.getString("active_session", null)
        set(v) = p.edit().putString("active_session", v).apply()

    var activePhase: String?
        get() = p.getString("active_phase", null)
        set(v) = p.edit().putString("active_phase", v).apply()

    var activeStartNs: Long
        get() = p.getLong("active_start_ns", 0L)
        set(v) = p.edit().putLong("active_start_ns", v).apply()

    var activeTargetStillS: Float
        get() = p.getFloat("active_target_still_s", 0f)
        set(v) = p.edit().putFloat("active_target_still_s", v).apply()
}

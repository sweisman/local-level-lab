// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.SharedPreferences
import java.util.UUID

class LllApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val ch = NotificationChannel(CHANNEL, getString(R.string.channel_recording), NotificationManager.IMPORTANCE_LOW)
        getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
    }

    companion object {
        const val CHANNEL = "recording"
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
        get() = p.getInt("cal_pos_min", 5)
        set(v) = p.edit().putInt("cal_pos_min", v.coerceIn(2, 15)).apply()

    var driftMinutes: Int
        get() = p.getInt("drift_min", 30)
        set(v) = p.edit().putInt("drift_min", v.coerceIn(10, 240)).apply()
}

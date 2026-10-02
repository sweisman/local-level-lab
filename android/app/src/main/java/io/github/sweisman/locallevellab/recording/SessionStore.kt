// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording

import android.content.Context
import android.os.Build
import android.os.SystemClock
import io.github.sweisman.locallevellab.BuildConfig
import io.github.sweisman.locallevellab.Prefs
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * A session lives in `files/sessions/<id>/`:
 *   manifest.json  (exactly what ships in the zip, see docs/FORMAT.md)
 *   local.json     (device-only state such as upload status, never uploaded)
 *   *.csv.gz       (raw streams, one gzip member appended per recording phase)
 */
class Session(val dir: File) {
    val id: String get() = dir.name
    val manifest: JSONObject = JSONObject(File(dir, "manifest.json").readText())
    val local: JSONObject = File(dir, "local.json").let { if (it.exists()) JSONObject(it.readText()) else JSONObject() }

    val phases: List<JSONObject>
        get() = manifest.getJSONArray("phases").let { a -> (0 until a.length()).map { a.getJSONObject(it) } }

    fun hasPhase(name: String) = phases.any { it.getString("name") == name }
    fun hasPhasePrefix(prefix: String) = phases.any { it.getString("name").startsWith(prefix) }

    val title: String
        get() = manifest.getJSONObject("flight").let {
            "${it.optString("airline")} ${it.optString("flight_number")}".trim().ifEmpty { "Untitled" } + " · " + it.optString("date")
        }

    val zipFile: File get() = File(dir, "lll_${id.take(8)}.zip")
    val finalized: Boolean get() = local.optBoolean("finalized") && zipFile.exists()

    fun sizeBytes(): Long = dir.listFiles()?.filter { it.name.endsWith(".gz") }?.sumOf { it.length() } ?: 0

    @Synchronized
    fun save() {
        File(dir, "manifest.json.tmp").apply { writeText(manifest.toString(1)); renameTo(File(dir, "manifest.json")) }
        File(dir, "local.json").writeText(local.toString())
    }
}

object SessionStore {
    fun root(ctx: Context) = File(ctx.filesDir, "sessions").apply { mkdirs() }

    fun list(ctx: Context): List<Session> =
        root(ctx).listFiles { f -> File(f, "manifest.json").exists() }
            ?.map { Session(it) }
            ?.sortedByDescending { it.manifest.optString("created_utc") } ?: emptyList()

    fun load(ctx: Context, id: String): Session? =
        File(root(ctx), id).takeIf { File(it, "manifest.json").exists() }?.let { Session(it) }

    fun create(ctx: Context, flight: JSONObject, mount: JSONObject): Session {
        val id = UUID.randomUUID().toString()
        val dir = File(root(ctx), id).apply { mkdirs() }
        val iso = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply { timeZone = TimeZone.getTimeZone("UTC") }
        val m = JSONObject()
            .put("schema_version", 1)
            .put("data_license", "CC0-1.0")
            .put("session_id", id)
            .put("install_id", Prefs(ctx).installId)
            .put("created_utc", iso.format(Date()))
            .put("app", JSONObject().put("name", "Local Level Lab").put("version", BuildConfig.VERSION_NAME).put("build", BuildConfig.VERSION_CODE))
            .put("device", JSONObject()
                .put("manufacturer", Build.MANUFACTURER).put("model", Build.MODEL)
                .put("android_sdk", Build.VERSION.SDK_INT).put("android_release", Build.VERSION.RELEASE))
            .put("sensors", JSONObject())
            .put("sampling_period_us", Recorder.SAMPLING_PERIOD_US)
            .put("clock", JSONObject().put("elapsed_ns", SystemClock.elapsedRealtimeNanos()).put("utc_ms", System.currentTimeMillis()))
            .put("flight", flight)
            .put("mount", mount)
            .put("privacy", JSONObject().put("cal_lat_deg", JSONObject.NULL))
            .put("phases", JSONArray())
            .put("quality", JSONObject().put("cal_pre", false).put("cal_post", false).put("placement_check", false).put("flags", JSONArray()))
        File(dir, "manifest.json").writeText(m.toString(1))
        return Session(dir)
    }

    fun addPhase(s: Session, name: String, startNs: Long, endNs: Long, stillS: Double) {
        s.manifest.getJSONArray("phases").put(
            JSONObject().put("name", name).put("start_ns", startNs).put("end_ns", endNs).put("still_s", stillS),
        )
        val q = s.manifest.getJSONObject("quality")
        if (s.hasPhasePrefix("cal_pre.") && s.phases.count { it.getString("name").startsWith("cal_pre.") } >= 4) q.put("cal_pre", true)
        if (s.phases.count { it.getString("name").startsWith("cal_post.") } >= 4) q.put("cal_post", true)
        if (name == "placement_check") q.put("placement_check", true)
        s.save()
    }

    fun addFlag(s: Session, flag: String) {
        val flags = s.manifest.getJSONObject("quality").getJSONArray("flags")
        if ((0 until flags.length()).none { flags.getString(it) == flag }) flags.put(flag)
        s.save()
    }

    /** Package the session into the upload/share zip. The raw files are copied byte for byte. */
    fun finalize(s: Session): File {
        val out = s.zipFile
        val tmp = File(s.dir, out.name + ".tmp")
        ZipOutputStream(tmp.outputStream().buffered()).use { zip ->
            zip.putNextEntry(ZipEntry("manifest.json"))
            zip.write(s.manifest.toString(1).toByteArray())
            zip.closeEntry()
            s.dir.listFiles { f -> f.name.endsWith(".csv.gz") }?.sortedBy { it.name }?.forEach { f ->
                zip.putNextEntry(ZipEntry(f.name))
                f.inputStream().use { it.copyTo(zip) }
                zip.closeEntry()
            }
        }
        tmp.renameTo(out)
        s.local.put("finalized", true)
        s.save()
        return out
    }

    fun delete(s: Session) = s.dir.deleteRecursively()
}

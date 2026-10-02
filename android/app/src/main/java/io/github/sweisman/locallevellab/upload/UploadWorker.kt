// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.upload

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import io.github.sweisman.locallevellab.Prefs
import io.github.sweisman.locallevellab.recording.SessionStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Sends one finalized session zip to the server as a multipart POST. This is the app's only network use. */
class UploadWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val id = inputData.getString(KEY_SESSION) ?: return@withContext Result.failure()
        val s = SessionStore.load(applicationContext, id) ?: return@withContext Result.failure()
        val base = Prefs(applicationContext).serverUrl
        if (base.isBlank()) {
            s.local.put("upload_error", "No server set in Settings"); s.save()
            return@withContext Result.failure()
        }
        val zip = if (s.finalized) s.zipFile else SessionStore.finalize(s)
        val boundary = "lll-" + UUID.randomUUID()
        val conn = (URL("$base/api/v1/sessions").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 30_000
            readTimeout = 120_000
            setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
            setChunkedStreamingMode(1 shl 16)
        }
        try {
            conn.outputStream.buffered().use { out ->
                out.write(("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"${zip.name}\"\r\n" +
                    "Content-Type: application/zip\r\n\r\n").toByteArray())
                zip.inputStream().use { it.copyTo(out) }
                out.write("\r\n--$boundary--\r\n".toByteArray())
            }
            val code = conn.responseCode
            val body = (if (code < 400) conn.inputStream else conn.errorStream)?.bufferedReader()?.readText() ?: ""
            when {
                code in 200..299 -> {
                    s.local.put("upload_id", JSONObject(body).optString("id")).put("uploaded_ms", System.currentTimeMillis())
                    s.local.remove("upload_error")
                    s.save()
                    Result.success()
                }
                code == 429 || code >= 500 -> Result.retry()
                else -> { s.local.put("upload_error", "HTTP $code: ${body.take(300)}"); s.save(); Result.failure() }
            }
        } catch (e: java.io.IOException) {
            s.local.put("upload_error", e.toString()); s.save()
            Result.retry()
        } finally {
            conn.disconnect()
        }
    }

    companion object {
        const val KEY_SESSION = "session"

        fun enqueue(ctx: Context, sessionId: String) {
            val net = if (Prefs(ctx).unmeteredOnly) NetworkType.UNMETERED else NetworkType.CONNECTED
            val req = OneTimeWorkRequestBuilder<UploadWorker>()
                .setConstraints(Constraints.Builder().setRequiredNetworkType(net).build())
                .setInputData(workDataOf(KEY_SESSION to sessionId))
                .build()
            WorkManager.getInstance(ctx).enqueueUniqueWork("upload-$sessionId", ExistingWorkPolicy.KEEP, req)
        }
    }
}

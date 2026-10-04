package io.github.sweisman.locallevellab.upload

import io.github.sweisman.locallevellab.recording.Session
import io.github.sweisman.locallevellab.recording.SessionStore
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.ZipFile

internal object UploadSnapshots {
    data class Prepared(val file: File, val workName: String, val digest: String, val manifestDigest: String)

    fun digest(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }

    private fun digest(file: File): String {
        val md = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { stream ->
            val buffer = ByteArray(65536)
            while (true) {
                val count = stream.read(buffer)
                if (count < 0) break
                md.update(buffer, 0, count)
            }
        }
        return md.digest().joinToString("") { "%02x".format(it) }
    }

    fun prepare(s: Session, destination: String, pending: (String) -> Boolean): Prepared? = synchronized(SessionStore) {
        val archive = SessionStore.finalize(s)
        val sha = digest(archive)
        val key = "upload-${s.id}-${digest(destination.toByteArray())}-$sha"
        if (pending(key)) return@synchronized null
        val snapshot = archive.copyTo(File(s.dir, "upload-${UUID.randomUUID()}.zip"))
        try {
            val manifest = ZipFile(snapshot).use { zip ->
                digest(zip.getInputStream(zip.getEntry("manifest.json")).use { it.readBytes() })
            }
            Prepared(snapshot, key, sha, manifest)
        } catch (e: Exception) {
            snapshot.delete()
            throw e
        }
    }

    fun complete(file: File, retry: Boolean) { if (!retry) file.delete() }
}

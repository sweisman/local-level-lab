package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.recording.Session
import io.github.sweisman.locallevellab.recording.SessionStore
import io.github.sweisman.locallevellab.upload.UploadSnapshots
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class UploadTest {
    @get:Rule val tmp = TemporaryFolder()

    private fun session(): Session {
        val dir = tmp.newFolder()
        File(dir, "manifest.json").writeText("{\"phases\":[],\"quality\":{\"flags\":[]}}")
        File(dir, "events.csv.journal").writeText("t_ns,kind,detail\n1,note,first\n")
        return Session(dir)
    }

    @Test fun pendingWorkIsReusedBySessionDestinationAndBytes() {
        val s = session()
        val first = UploadSnapshots.prepare(s, "https://example.org") { false }!!
        // Force an archive mtime change; packaging must still have the same digest.
        s.zipFile.setLastModified(0)
        assertNull(UploadSnapshots.prepare(s, "https://example.org") { it == first.workName })
        val other = UploadSnapshots.prepare(s, "https://other.example.org") { it == first.workName }!!
        assertNotEquals(first.workName, other.workName)
        File(s.dir, "events.csv.journal").appendText("2,note,next\n")
        val changed = UploadSnapshots.prepare(s, "https://example.org") { it == first.workName }!!
        assertNotEquals(first.digest, changed.digest)
    }

    @Test fun retriesRetainBytesAndTerminalCleanupPreservesAcknowledgement() {
        val s = session()
        val p = UploadSnapshots.prepare(s, "https://example.org") { false }!!
        val bytes = p.file.readBytes()
        UploadSnapshots.complete(p.file, retry = true)
        assertArrayEquals(bytes, p.file.readBytes())
        s.local.put("upload_id", "ack").put("upload_sha256", p.digest)
            .put("upload_manifest_sha256", p.manifestDigest).put("uploaded_ms", 1L)
        SessionStore.updateUpload(s)
        UploadSnapshots.complete(p.file, retry = false)
        SessionStore.updateUpload(s)
        val restored = Session(s.dir)
        assertFalse(p.file.exists())
        assertEquals("ack", restored.local.getString("upload_id"))
        assertEquals(p.digest, restored.local.getString("upload_sha256"))
        val cancelled = UploadSnapshots.prepare(restored, "https://example.org") { false }!!
        UploadSnapshots.complete(cancelled.file, retry = false)
        assertFalse(cancelled.file.exists())
    }
}

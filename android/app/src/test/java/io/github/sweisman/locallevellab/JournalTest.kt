package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.recording.Journal
import io.github.sweisman.locallevellab.recording.Session
import io.github.sweisman.locallevellab.recording.SessionStore
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.GZIPInputStream
import java.util.zip.ZipFile

class JournalTest {
    @get:Rule val tmp = TemporaryFolder()

    @Test fun interruptedBinaryRecordPreservesCompleteRecords() {
        val f = tmp.newFile()
        val record = ByteBuffer.allocate(13).order(ByteOrder.LITTLE_ENDIAN).putLong(42).putShort(3).put(byteArrayOf(1, 2, 3)).array()
        f.writeBytes(record + record.copyOf(11))
        assertEquals(11L, Journal.repair(f, true))
        assertArrayEquals(record, f.readBytes())
        assertEquals(0L, Journal.repair(f, true))
    }

    @Test fun interruptedCsvDropsOnlyUnfinishedLine() {
        val f = tmp.newFile()
        f.writeText("t_ns,kind,detail\n1,event,complete\n2,partial")
        assertEquals(9L, Journal.repair(f, false))
        assertEquals("t_ns,kind,detail\n1,event,complete\n", f.readText())
    }

    @Test fun repackagingIncludesLaterJournalDataAndRefusesActiveRecording() {
        val dir = tmp.newFolder()
        java.io.File(dir, "manifest.json").writeText("{\"phases\":[],\"quality\":{\"flags\":[]}}")
        val journal = java.io.File(dir, "events.csv.journal")
        journal.writeText("t_ns,kind,detail\n1,note,first\n")
        val s = Session(dir)
        SessionStore.finalize(s)
        journal.appendText("2,note,later\n")
        ZipFile(SessionStore.finalize(s)).use { zip ->
            val text = GZIPInputStream(zip.getInputStream(zip.getEntry("events.csv.gz"))).bufferedReader().readText()
            assertTrue(text.endsWith("2,note,later\n"))
        }
        java.io.File(dir, "recording.marker").writeText("flight")
        assertThrows(IllegalStateException::class.java) { SessionStore.finalize(s) }
    }
}

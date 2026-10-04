package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.recording.RecoveryLoop
import org.junit.Assert.*
import org.junit.Test

class RecoveryTest {
    @Test fun delayedBluetoothAndConfigurationResumeAfterRestart() {
        val scheduled = mutableListOf<Runnable>()
        val loop = RecoveryLoop({ scheduled.add(it) }, { scheduled.remove(it) })
        var verified = false
        var recording = false
        fun resume() {
            if (verified) recording = true else loop.awaitConfiguration { resume() }
        }
        resume() // persisted phase restored after process death
        repeat(3) {
            assertTrue(loop.waiting) // service must retain foreground/link while waiting
            scheduled.removeAt(0).run()
            assertFalse(recording)
        }
        verified = true
        scheduled.removeAt(0).run()
        assertTrue(recording)
        assertFalse(loop.waiting)
    }

    @Test fun explicitStopInvalidatesEvenAnAlreadyQueuedRestart() {
        val scheduled = mutableListOf<Runnable>()
        val loop = RecoveryLoop({ scheduled.add(it) }, { scheduled.remove(it) })
        var restarted = false
        loop.awaitConfiguration { restarted = true }
        val stale = scheduled.single()
        loop.clear()
        stale.run()
        assertFalse(restarted)
        assertFalse(loop.waiting)
        assertTrue(scheduled.isEmpty())
    }
}

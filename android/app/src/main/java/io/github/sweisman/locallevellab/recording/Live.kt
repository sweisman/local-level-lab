// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording

import io.github.sweisman.locallevellab.model.Transport
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlin.math.acos
import kotlin.math.sqrt

object Recorder {
    /** 100 Hz, below Android 12's 200 Hz cap that needs HIGH_SAMPLING_RATE_SENSORS. */
    const val SAMPLING_PERIOD_US = 10_000
}

/** Snapshot for the UI. Display only: nothing here is written to a session. */
data class LiveState(
    val sessionId: String? = null,
    val phase: String? = null,
    val elapsedS: Double = 0.0,
    val stillS: Double = 0.0,
    val stillStreakS: Double = 0.0,
    val isStill: Boolean = false,
    val targetStillS: Double = 0.0,
    val lastCompletedPhase: String? = null,
    val gravityAxis: String = "",
    val gravity: FloatArray = FloatArray(3),
    val tiltShiftDeg: Double = 0.0,
    val accelSd: Double = 0.0,
    val gyroSdDps: Double = 0.0,
    val samples: Map<String, Long> = emptyMap(),
    val hasFix: Boolean = false,
    val speedMps: Double = 0.0,
    val altM: Double = 0.0,
    val bearingDeg: Double = 0.0,
    val latDeg: Double = 0.0,
    val sats: Int = 0,
    val hAccM: Double = 0.0,
    val predictedDph: Map<Transport.Model, Double> = emptyMap(),
    val transportDph: Double = 0.0,
    val accumulatedDeg: Map<Transport.Model, Double> = emptyMap(),
    val transportAccumDeg: Double = 0.0,
    val measuredDph: Double? = null,
    val shiftWarning: Boolean = false,
    val error: String? = null,
)

object Live {
    val state = MutableStateFlow(LiveState())
    val flow: StateFlow<LiveState> get() = state
}

/**
 * Rolling 1-s block statistics for the stillness gate, the placement check and the rough live
 * "measured" rate.
 */
class BlockStats(private val stillAccelSd: Double, private val stillGyroSd: Double) {
    private var n = 0
    private val aSum = DoubleArray(3)
    private var aMagSum = 0.0
    private var aMagSq = 0.0
    private val gSum = DoubleArray(3)
    private val gSq = DoubleArray(3)
    private var gn = 0

    var lastAccelSd = 0.0; private set
    var lastGyroSd = 0.0; private set
    var lastAccelMean = DoubleArray(3); private set
    var lastGyroMean = DoubleArray(3); private set

    fun accel(x: Float, y: Float, z: Float) {
        aSum[0] += x; aSum[1] += y; aSum[2] += z
        val m = sqrt((x * x + y * y + z * z).toDouble())
        aMagSum += m; aMagSq += m * m; n++
    }

    fun gyro(x: Float, y: Float, z: Float) {
        gSum[0] += x; gSum[1] += y; gSum[2] += z
        gSq[0] += x.toDouble() * x; gSq[1] += y.toDouble() * y; gSq[2] += z.toDouble() * z
        gn++
    }

    /** Close the block. Returns true if this second was still. */
    fun close(): Boolean {
        if (n < 5 || gn < 5) { reset(); return false }
        lastAccelMean = DoubleArray(3) { aSum[it] / n }
        lastGyroMean = DoubleArray(3) { gSum[it] / gn }
        lastAccelSd = sqrt(maxOf(0.0, aMagSq / n - (aMagSum / n) * (aMagSum / n)))
        lastGyroSd = sqrt((0..2).sumOf { maxOf(0.0, gSq[it] / gn - lastGyroMean[it] * lastGyroMean[it]) })
        reset()
        return lastAccelSd < stillAccelSd && lastGyroSd < stillGyroSd
    }

    private fun reset() {
        n = 0; gn = 0; aMagSum = 0.0; aMagSq = 0.0
        aSum.fill(0.0); gSum.fill(0.0); gSq.fill(0.0)
    }

    companion object {
        fun angleDeg(a: DoubleArray, b: DoubleArray): Double {
            val na = sqrt(a.sumOf { it * it }); val nb = sqrt(b.sumOf { it * it })
            if (na == 0.0 || nb == 0.0) return 0.0
            val c = ((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (na * nb)).coerceIn(-1.0, 1.0)
            return Math.toDegrees(acos(c))
        }
    }
}

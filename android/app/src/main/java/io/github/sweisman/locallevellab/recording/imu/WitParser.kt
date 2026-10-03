// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording.imu

/** The two supported WitMotion WT901 variants. `key` is what the session manifest stores. */
enum class Variant(val key: String, val model: String) {
    SPP("spp", "WT901SDCL ICM-42605 / MMC3630, Bluetooth 2.0 serial"),
    BLE("ble", "WT901SDCL MPU9250, Bluetooth LE 5.0");

    companion object {
        fun of(key: String?) = entries.firstOrNull { it.key == key }
    }
}

/**
 * Decodes the WitMotion byte stream for the live display, the stillness gate and the config
 * readback. Display only: the session stores the raw bytes, and analysis/lll/witmotion.py is the
 * decoder of record. Both are tested against docs/test_vectors.json.
 *
 * Not thread-safe; feed it from one thread.
 */
class WitParser(
    private val variant: Variant,
    private val gyroRangeDps: Double = 2000.0,
    private val accelRangeG: Double = 16.0,
) {
    interface Sink {
        fun gyro(x: Double, y: Double, z: Double) {}    // rad/s
        fun accel(x: Double, y: Double, z: Double) {}   // m/s²
        fun mag(x: Double, y: Double, z: Double) {}     // raw counts
        fun tempC(t: Double) {}
        fun volt(v: Double) {}
        /** Register readback: `values` are consecutive registers starting at `start`. */
        fun registers(start: Int, values: IntArray) {}
    }

    var packets = 0L; private set
    var badChecksums = 0L; private set
    var skippedBytes = 0L; private set

    private val buf = ByteArray(4096)
    private var n = 0

    fun feed(data: ByteArray, len: Int = data.size, sink: Sink) {
        if (variant == Variant.BLE) { feedBle(data, len, sink); return }
        var i = 0
        while (i < len) {
            val take = minOf(len - i, buf.size - n)
            System.arraycopy(data, i, buf, n, take)
            n += take; i += take
            n = drainSpp(sink)
        }
    }

    private fun u8(b: ByteArray, i: Int) = b[i].toInt() and 0xFF
    private fun i16(b: ByteArray, i: Int) = ((b[i + 1].toInt() shl 8) or (b[i].toInt() and 0xFF)).toShort().toInt()

    /** Consume whole SPP packets from buf; returns the number of bytes left over. */
    private fun drainSpp(sink: Sink): Int {
        var p = 0
        while (n - p >= 11) {
            val t = u8(buf, p + 1)
            if (u8(buf, p) != 0x55 || t !in SPP_TYPES) { p++; skippedBytes++; continue }
            var sum = 0
            for (k in 0 until 10) sum += u8(buf, p + k)
            if ((sum and 0xFF) != u8(buf, p + 10)) { badChecksums++; p++; skippedBytes++; continue }
            spp(t, p + 2, sink)
            packets++
            p += 11
        }
        val rest = n - p
        System.arraycopy(buf, p, buf, 0, rest)
        return rest
    }

    private fun spp(type: Int, d: Int, sink: Sink) {
        val v = IntArray(4) { i16(buf, d + 2 * it) }
        when (type) {
            0x51 -> { sink.accel(acc(v[0]), acc(v[1]), acc(v[2])); sink.tempC(v[3] / 100.0) }
            0x52 -> { sink.gyro(gyr(v[0]), gyr(v[1]), gyr(v[2])); sink.volt(v[3] / 100.0) }
            0x54 -> { sink.mag(v[0].toDouble(), v[1].toDouble(), v[2].toDouble()); sink.tempC(v[3] / 100.0) }
            0x5F -> sink.registers(lastReadRegister, v)
        }
    }

    /** The serial readback (0x5F) doesn't say which register it answers; WitConfig sets this. */
    var lastReadRegister = -1

    private fun feedBle(data: ByteArray, len: Int, sink: Sink) {
        var i = 0
        while (i + 20 <= len) {
            if (u8(data, i) == 0x55 && u8(data, i + 1) == 0x61) {
                val v = IntArray(9) { i16(data, i + 2 + 2 * it) }
                sink.accel(acc(v[0]), acc(v[1]), acc(v[2]))
                sink.gyro(gyr(v[3]), gyr(v[4]), gyr(v[5]))
                packets++; i += 20
            } else if (u8(data, i) == 0x55 && u8(data, i + 1) == 0x71) {
                val start = i16(data, i + 2)
                val v = IntArray(8) { i16(data, i + 4 + 2 * it) }
                if (start == REG_MAG) {
                    sink.mag(v[0].toDouble(), v[1].toDouble(), v[2].toDouble())
                    sink.tempC(v[6] / 100.0)
                }
                sink.registers(start, v)
                packets++; i += 20
            } else { i++; skippedBytes++ }
        }
        skippedBytes += (len - i).toLong()
    }

    private fun gyr(raw: Int) = Math.toRadians(raw / 32768.0 * gyroRangeDps)
    private fun acc(raw: Int) = raw / 32768.0 * accelRangeG * G0

    companion object {
        const val G0 = 9.80665
        const val REG_MAG = 0x3A
        val SPP_TYPES = setOf(0x50, 0x51, 0x52, 0x53, 0x54, 0x59, 0x5F)
    }
}

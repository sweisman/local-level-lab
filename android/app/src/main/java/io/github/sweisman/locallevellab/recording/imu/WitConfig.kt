// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording.imu

/**
 * WitMotion configuration commands (`FF AA reg lo hi`), from the published WIT protocol.
 *
 * UNVERIFIED until the Phase 0 bench test: register numbers, rate codes, the content mask and
 * above all the polarity of the automatic gyro zeroing register. If auto-zero stays on, the
 * device subtracts any slow rotation it sees while still, including the Earth's, so a readback
 * of every setting is logged with each recording.
 */
object WitConfig {
    const val REG_SAVE = 0x00
    const val REG_RSW = 0x02          // which packets the device sends
    const val REG_RATE = 0x03         // output rate code
    const val REG_GYRO_AUTO = 0x63    // automatic gyro zeroing: 0x01 = off (verify on bench)
    const val REG_GYRO_RANGE = 0x20   // gyro full scale: 0 = ±250, 1 = ±500, 2 = ±1000, 3 = ±2000 °/s (verify on bench)
    const val REG_ACC_RANGE = 0x21    // accelerometer full scale: 0 = ±2, 1 = ±4, 2 = ±8, 3 = ±16 g (verify on bench)
    const val GYRO_AUTO_OFF = 0x01
    const val GYRO_AUTO_ON = 0x00     // bench test of the polarity only; never used while flying

    /** RSW bits: 0x50 time, 0x51 accel, 0x52 gyro, 0x54 mag. Angle (0x53) and quaternion (0x59) are off. */
    const val RSW_SCIENCE = (1 shl 0) or (1 shl 1) or (1 shl 2) or (1 shl 4)

    val RATE_CODES = linkedMapOf(10 to 0x06, 20 to 0x07, 50 to 0x08, 100 to 0x09, 200 to 0x0B)
    val RANGE_CODES = linkedMapOf(250 to 0, 500 to 1, 1000 to 2, 2000 to 3)
    val ACC_RANGE_CODES = linkedMapOf(2 to 0, 4 to 1, 8 to 2, 16 to 3)

    fun cmd(reg: Int, value: Int) = byteArrayOf(0xFF.toByte(), 0xAA.toByte(), reg.toByte(), (value and 0xFF).toByte(), (value shr 8 and 0xFF).toByte())

    val UNLOCK = byteArrayOf(0xFF.toByte(), 0xAA.toByte(), 0x69, 0x88.toByte(), 0xB5.toByte())
    val SAVE = cmd(REG_SAVE, 0)

    fun read(reg: Int) = cmd(0x27, reg)

    /** The write sequence for a variant at a rate. Each write is preceded by an unlock. */
    fun apply(variant: Variant, rateHz: Int, gyroRangeDps: Int, accelRangeG: Int, autoZeroOn: Boolean = false): List<ByteArray> {
        val out = ArrayList<ByteArray>()
        fun w(reg: Int, v: Int) { out += UNLOCK; out += cmd(reg, v) }
        if (variant == Variant.SPP) w(REG_RSW, RSW_SCIENCE)
        w(REG_RATE, RATE_CODES[rateHz] ?: error("unsupported rate $rateHz Hz"))
        w(REG_GYRO_AUTO, if (autoZeroOn) GYRO_AUTO_ON else GYRO_AUTO_OFF)
        w(REG_GYRO_RANGE, RANGE_CODES[gyroRangeDps] ?: error("unsupported gyro range $gyroRangeDps °/s"))
        w(REG_ACC_RANGE, ACC_RANGE_CODES[accelRangeG] ?: error("unsupported accel range $accelRangeG g"))
        out += UNLOCK; out += SAVE
        return out
    }

    /** Registers read back after configuring, with the value each should hold. */
    fun expected(variant: Variant, rateHz: Int, gyroRangeDps: Int, accelRangeG: Int, autoZeroOn: Boolean = false): Map<Int, Int> = buildMap {
        if (variant == Variant.SPP) put(REG_RSW, RSW_SCIENCE)
        put(REG_RATE, RATE_CODES.getValue(rateHz))
        put(REG_GYRO_AUTO, if (autoZeroOn) GYRO_AUTO_ON else GYRO_AUTO_OFF)
        put(REG_GYRO_RANGE, RANGE_CODES.getValue(gyroRangeDps))
        put(REG_ACC_RANGE, ACC_RANGE_CODES.getValue(accelRangeG))
    }

    /** BLE only: poll the magnetometer and temperature registers (reply 0x55 0x71 from 0x3A). */
    val POLL_MAG_TEMP = read(WitParser.REG_MAG)
}

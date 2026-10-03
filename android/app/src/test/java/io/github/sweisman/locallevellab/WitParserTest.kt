// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.recording.imu.Variant
import io.github.sweisman.locallevellab.recording.imu.WitParser
import org.json.JSONObject
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** Checks the live-display parser against the same packets the Python decoder is tested on. */
class WitParserTest {
    private val vec: JSONObject by lazy {
        var dir: File? = File("").absoluteFile
        while (dir != null && !File(dir, "docs/test_vectors.json").exists()) dir = dir.parentFile
        JSONObject(File(dir!!, "docs/test_vectors.json").readText()).getJSONObject("witmotion")
    }

    private fun hex(s: String) = ByteArray(s.length / 2) { s.substring(2 * it, 2 * it + 2).toInt(16).toByte() }

    private class Rec : WitParser.Sink {
        val gyro = ArrayList<DoubleArray>(); val accel = ArrayList<DoubleArray>(); val mag = ArrayList<DoubleArray>()
        val temp = ArrayList<Double>(); val volt = ArrayList<Double>()
        override fun gyro(x: Double, y: Double, z: Double) { gyro += doubleArrayOf(x, y, z) }
        override fun accel(x: Double, y: Double, z: Double) { accel += doubleArrayOf(x, y, z) }
        override fun mag(x: Double, y: Double, z: Double) { mag += doubleArrayOf(x, y, z) }
        override fun tempC(t: Double) { temp += t }
        override fun volt(v: Double) { volt += v }
    }

    private fun expect(name: String, key: String) =
        (0 until vec.getJSONArray(name).length()).map { vec.getJSONArray(name).getJSONObject(it) }
            .first { it.getString("type") == key }.getJSONObject("expect")

    private fun arr(o: JSONObject, k: String, scale: Double = 1.0) =
        o.getJSONArray(k).let { a -> DoubleArray(a.length()) { a.getDouble(it) * scale } }

    private fun sppCycle(): ByteArray {
        val a = vec.getJSONArray("spp")
        return (0 until a.length()).map { hex(a.getJSONObject(it).getString("hex")) }.reduce { x, y -> x + y }
    }

    @Test
    fun sppVectors() {
        val r = Rec()
        WitParser(Variant.SPP).feed(sppCycle(), sink = r)
        assertArrayEquals(arr(expect("spp", "gyro"), "gyro_dps").map { Math.toRadians(it) }.toDoubleArray(), r.gyro[0], 1e-12)
        assertArrayEquals(arr(expect("spp", "accel"), "accel_g", WitParser.G0), r.accel[0], 1e-9)
        assertArrayEquals(arr(expect("spp", "mag"), "mag_counts"), r.mag[0], 0.0)
        assertEquals(expect("spp", "accel").getDouble("temp_c"), r.temp[0], 1e-9)
        assertEquals(expect("spp", "gyro").getDouble("volt"), r.volt[0], 1e-9)
    }

    @Test
    fun sppRejectsBadChecksumResyncsAndJoinsSplitReads() {
        val good = sppCycle()
        val data = byteArrayOf(0x55, 0x52, 0x01) + hex(vec.getString("spp_bad_checksum")) + good + byteArrayOf(0, 0x55) + good
        val p = WitParser(Variant.SPP)
        val r = Rec()
        var i = 0
        for (cut in listOf(5, 17, 40, 41, 100, data.size)) { p.feed(data.copyOfRange(i, cut), sink = r); i = cut }
        assertEquals(2, r.gyro.size)
        assertEquals(2L, p.badChecksums)  // the junk "55 52 01" and the corrupt packet both look like headers
    }

    @Test
    fun bleVectors() {
        val a = vec.getJSONArray("ble")
        val r = Rec()
        val p = WitParser(Variant.BLE)
        for (k in 0 until a.length()) p.feed(hex(a.getJSONObject(k).getString("hex")), sink = r)
        val d = expect("ble", "data"); val g = expect("ble", "reg")
        assertArrayEquals(arr(d, "accel_g", WitParser.G0), r.accel[0], 1e-9)
        assertArrayEquals(arr(d, "gyro_dps").map { Math.toRadians(it) }.toDoubleArray(), r.gyro[0], 1e-12)
        assertArrayEquals(arr(g, "mag_counts"), r.mag[0], 0.0)
        assertEquals(g.getDouble("temp_c"), r.temp[0], 1e-9)
    }
}

// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.model.Transport
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** Checks the Kotlin math against the same vectors the Python analysis is tested on. */
class TransportTest {
    private val vectors: JSONObject by lazy {
        var dir: File? = File("").absoluteFile
        while (dir != null && !File(dir, "docs/test_vectors.json").exists()) dir = dir.parentFile
        JSONObject(File(dir!!, "docs/test_vectors.json").readText())
    }

    @Test
    fun transportRateMatchesSharedVectors() {
        val arr = vectors.getJSONArray("transport")
        for (i in 0 until arr.length()) {
            val v = arr.getJSONObject(i)
            val got = Transport.transportRate(
                Math.toRadians(v.getDouble("lat_deg")), v.getDouble("h_m"), v.getDouble("v_n"), v.getDouble("v_e"),
            )
            val exp = v.getJSONArray("omega_en")
            for (k in 0..2) assertEquals(v.getString("name"), exp.getDouble(k), got[k], 1e-12 + 1e-9 * Math.abs(exp.getDouble(k)))
        }
    }

    @Test
    fun earthRateMatchesSharedVectors() {
        val arr = vectors.getJSONArray("earth_rate")
        for (i in 0 until arr.length()) {
            val v = arr.getJSONObject(i)
            val got = Transport.earthRateSphere(Math.toRadians(v.getDouble("lat_deg")))
            val exp = v.getJSONArray("sphere")
            for (k in 0..2) assertEquals(exp.getDouble(k), got[k], 1e-15)
            val flat = v.getJSONArray("flat")
            for (k in 0..2) assertEquals(flat.getDouble(k), Transport.earthRateFlat()[k], 1e-15)
        }
    }

    @Test
    fun headlineNumbers() {
        val w = Transport.transportRate(0.0, 0.0, 224.0, 0.0)
        assertEquals(7.29, Math.abs(w[1]) * Transport.RAD_TO_DEG_PER_HOUR, 0.01)
        assertEquals(15.041, Transport.OMEGA_E * Transport.RAD_TO_DEG_PER_HOUR, 0.001)
    }
}

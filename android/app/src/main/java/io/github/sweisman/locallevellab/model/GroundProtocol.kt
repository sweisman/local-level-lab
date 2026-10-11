// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.model

import org.json.JSONObject

object GroundProtocol {
    const val VERSION = "stationary-reversal-v1"
    val positions = listOf("A", "B", "B", "A", "A", "B", "B", "A")
    val steps = positions.mapIndexed { i, position -> "ground.$position.${i + 1}" }
    fun valid(m: JSONObject): Boolean {
        if (m.optString("axis") !in listOf("x", "y")) return false
        val ranges = mapOf("latitude_deg" to (-90.0..90.0), "longitude_deg" to (-180.0..180.0),
            "altitude_m" to (-500.0..10000.0), "heading_true_deg" to (0.0..360.0),
            "heading_uncertainty_deg" to (0.0..180.0), "block_minutes" to (10.0..120.0))
        return ranges.all { (key, range) -> !m.has(key) ||
            (m.opt(key) is Number && m.optDouble(key).isFinite() && m.optDouble(key) in range) }
    }
}

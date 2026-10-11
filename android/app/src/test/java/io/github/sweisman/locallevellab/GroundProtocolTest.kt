// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.model.GroundProtocol
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class GroundProtocolTest {
    @Test fun repeatedBlocksBalanceLinearDrift() {
        assertEquals(listOf("A", "B", "B", "A", "A", "B", "B", "A"), GroundProtocol.positions)
        assertEquals(0, GroundProtocol.positions.mapIndexed { i, p -> (if (p == "A") 1 else -1) * i }.sum())
    }
    @Test fun locationAndAxisMustBePhysicallyValid() {
        assertTrue(GroundProtocol.valid(JSONObject().put("axis", "x").put("latitude_deg", -45.0)))
        assertFalse(GroundProtocol.valid(JSONObject().put("axis", "z")))
        assertFalse(GroundProtocol.valid(JSONObject().put("axis", "x").put("latitude_deg", 91.0)))
        assertFalse(GroundProtocol.valid(JSONObject().put("axis", "x").put("heading_uncertainty_deg", -1.0)))
    }
}

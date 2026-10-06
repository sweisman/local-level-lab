package io.github.sweisman.locallevellab

import io.github.sweisman.locallevellab.model.Airline
import io.github.sweisman.locallevellab.model.AirlineDirectory
import io.github.sweisman.locallevellab.model.FlightIdentity
import org.junit.Assert.*
import org.junit.Test
import java.io.File

class FlightIdentityTest {
    private val etihad = Airline("test", "Etihad Airways", "", "EY", "ETD", "United Arab Emirates", true)

    @Test fun operatingCarrierNumberMustMatchSelectedCarrier() {
        assertEquals("EY10", etihad.number("10"))
        assertEquals("EY10", etihad.number(" ey 10 "))
        assertEquals("EY10A", etihad.number("ETD10A"))
        assertNull(etihad.number("AA10"))
        assertNull(etihad.number("0"))
        assertNull(etihad.number("10/11"))
        val indigo = etihad.copy(iata = "6E", icao = "IGO")
        assertEquals("6E123", indigo.number("6E123"))
        assertEquals("6E6123", indigo.number("6123"))
        val icaoOnly = etihad.copy(iata = "")
        assertEquals("ETD10", icaoOnly.number("10"))
        assertEquals("https://www.flightaware.com/live/flight/ETD10/history", etihad.historyUrl("EY10"))
    }

    @Test fun identityNeedsActualCalendarDateAndDifferentAirportCodes() {
        assertTrue(FlightIdentity.valid(etihad, "10", "2024-02-29", "ord", "auh"))
        assertFalse(FlightIdentity.valid(etihad, "10", "2025-02-29", "ORD", "AUH"))
        assertFalse(FlightIdentity.valid(etihad, "10", "2025-2-19", "ORD", "AUH"))
        assertFalse(FlightIdentity.valid(etihad, "10", "2025-08-19", "ORD", "ord"))
        assertFalse(FlightIdentity.valid(etihad, "10", "2025-08-19", "Chicago", "AUH"))
        assertFalse(FlightIdentity.valid(null, "10", "2025-08-19", "ORD", "AUH"))
    }

    @Test fun bundledDirectoryIsBroadAndKeepsSharedCodesDistinct() {
        val directory = AirlineDirectory.read(File("src/main/assets/airlines.json").readText())
        assertTrue(directory.airlines.size > 5000)
        for ((code, name) in listOf("EY" to "Etihad Airways", "AA" to "American Airlines", "EK" to "Emirates")) {
            assertEquals(name, directory.search(code).first().name)
        }
        val lufthansa = directory.search("LH").filter { it.iata == "LH" }
        assertTrue(lufthansa.any { it.name == "Lufthansa" })
        assertTrue(lufthansa.any { it.name == "Lufthansa Cargo" })
        assertEquals(lufthansa.size, lufthansa.map { it.id }.distinct().size)
        assertTrue(directory.search("etihad emirates").any { it.name == "Etihad Airways" })
        assertTrue(directory.search("not-a-real-airline-xyz").isEmpty())
    }
}

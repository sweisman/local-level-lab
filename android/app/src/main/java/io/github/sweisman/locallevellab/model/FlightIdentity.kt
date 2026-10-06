// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.model

import org.json.JSONObject
import java.time.LocalDate
import java.util.Locale

data class Airline(
    val id: String, val name: String, val alias: String, val iata: String,
    val icao: String, val country: String, val listedActive: Boolean,
) {
    val label: String get() = "$name (${listOf(iata, icao).filter { it.isNotEmpty() }.joinToString(" / ")}) — $country"
    val lookupCode: String get() = icao.ifEmpty { iata }
    fun number(input: String): String? {
        var number = input.trim().uppercase(Locale.ROOT).replace(" ", "")
        listOf(icao, iata).filter { it.isNotEmpty() }.firstOrNull { number.startsWith(it) }
            ?.let { number = number.removePrefix(it) }
        if (!Regex("[0-9]{1,4}[A-Z]?").matches(number) || number.takeWhile { it.isDigit() }.toInt() == 0) return null
        return iata.ifEmpty { icao } + number
    }
    fun historyUrl(input: String): String? = number(input)?.let {
        val prefix = iata.ifEmpty { icao }
        "https://www.flightaware.com/live/flight/$lookupCode${it.removePrefix(prefix)}/history"
    }
}

class AirlineDirectory(val revision: String, val airlines: List<Airline>) {
    fun search(query: String): List<Airline> {
        val tokens = query.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
        return airlines.filter { airline ->
            val text = "${airline.label} ${airline.alias}"
            tokens.all { text.contains(it, ignoreCase = true) }
        }.sortedWith(compareByDescending<Airline> {
            query.isNotBlank() && (it.iata.equals(query.trim(), true) || it.icao.equals(query.trim(), true))
        }.thenByDescending { it.listedActive }.thenBy { it.name.lowercase(Locale.ROOT) }.thenBy { it.id })
    }

    companion object {
        fun read(text: String): AirlineDirectory {
            val json = JSONObject(text)
            val entries = json.getJSONArray("airlines")
            val airlines = (0 until entries.length()).map { index ->
                val row = entries.getJSONObject(index)
                Airline(row.getString("id"), row.getString("name"), row.getString("alias"),
                    row.getString("iata"), row.getString("icao"), row.getString("country"), row.getBoolean("listed_active"))
            }
            require(airlines.isNotEmpty() && airlines.map { it.id }.distinct().size == airlines.size)
            require(airlines.all { Regex("[A-Z0-9]{2}").matches(it.iata) || Regex("[A-Z]{3}").matches(it.icao) })
            return AirlineDirectory(json.getString("source_revision"), airlines)
        }
    }
}

object FlightIdentity {
    fun valid(airline: Airline?, number: String, date: String, origin: String, destination: String): Boolean {
        if (airline?.number(number) == null) return false
        if (!Regex("[0-9]{4}-[0-9]{2}-[0-9]{2}").matches(date.trim()) ||
            runCatching { LocalDate.parse(date.trim()) }.isFailure) return false
        val from = origin.trim().uppercase(Locale.ROOT)
        val to = destination.trim().uppercase(Locale.ROOT)
        return Regex("[A-Z]{3}").matches(from) && Regex("[A-Z]{3}").matches(to) && from != to
    }
}

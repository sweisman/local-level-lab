// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.github.sweisman.locallevellab.model.Airline
import io.github.sweisman.locallevellab.model.AirlineDirectory

@Composable
fun AirlinePicker(directory: AirlineDirectory?, selected: Airline?, onSelect: (Airline) -> Unit) {
    var open by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf("") }
    OutlinedButton({ open = true }, Modifier.fillMaxWidth(), enabled = directory != null) {
        Text(selected?.label ?: "Choose operating airline (required)")
    }
    if (directory == null) Text("The airline directory could not be loaded. Flight sessions require the bundled directory.")
    if (open && directory != null) {
        val matches = remember(query, directory) { directory.search(query) }
        AlertDialog(onDismissRequest = { open = false }, title = { Text("Operating airline") }, text = {
            Column {
                OutlinedTextField(query, { query = it }, label = { Text("Name, airline code or country") }, singleLine = true)
                Text("${matches.size} matches. Choose the airline operating the aircraft, including on codeshares.")
                Column(Modifier.height(320.dp).verticalScroll(rememberScrollState())) {
                    matches.take(30).forEach { airline ->
                        TextButton({ onSelect(airline); open = false }, Modifier.fillMaxWidth()) { Text(airline.label) }
                    }
                }
                if (matches.size > 30) Text("Refine your search to see more matches.")
                if (matches.isEmpty()) Text("No matching airline. Check its IATA/ICAO code; a missing carrier needs a directory update.")
                Text("Directory: OpenFlights (ODbL). Listing does not verify a flight or current airline status.")
            }
        }, confirmButton = { TextButton({ open = false }) { Text("Close") } })
    }
}

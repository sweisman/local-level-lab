// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import io.github.sweisman.locallevellab.Prefs

/** Pure-black dark theme: easy on OLED batteries and on fellow passengers at night. */
private val Scheme = darkColorScheme(
    primary = Color(0xFF7EC8FF), onPrimary = Color.Black,
    secondary = Color(0xFFB0BEC5), background = Color.Black, surface = Color.Black,
    surfaceVariant = Color(0xFF161B22), onSurface = Color(0xFFE6EDF3), onSurfaceVariant = Color(0xFF9AA4AE),
    error = Color(0xFFFF7B72),
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val start = if (Prefs(this).consented) "home" else "consent"
        setContent {
            MaterialTheme(colorScheme = Scheme) {
                Box(Modifier.fillMaxSize().background(Color.Black).safeDrawingPadding()) { AppNav(start) }
            }
        }
    }
}

@Composable
fun AppNav(start: String) {
    val nav = rememberNavController()
    val idArg = listOf(navArgument("id") { type = NavType.StringType })
    NavHost(nav, startDestination = start) {
        composable("consent") { ConsentScreen(onDone = { nav.navigate("home") { popUpTo("consent") { inclusive = true } } }, nav = nav) }
        composable("home") { HomeScreen(nav) }
        composable("instructions?section={section}", listOf(navArgument("section") { nullable = true; defaultValue = null })) {
            InstructionsScreen(it.arguments?.getString("section"), nav)
        }
        composable("settings") { SettingsScreen(nav) }
        composable("new") { NewSessionScreen(nav) }
        composable("session/{id}", idArg) { SessionScreen(it.arguments!!.getString("id")!!, nav) }
        composable("cal/{id}/{which}", idArg + navArgument("which") { type = NavType.StringType }) {
            CalibrationScreen(it.arguments!!.getString("id")!!, it.arguments!!.getString("which")!!, nav)
        }
        composable("still/{id}/{name}", idArg + navArgument("name") { type = NavType.StringType }) {
            DriftScreen(it.arguments!!.getString("id")!!, it.arguments!!.getString("name")!!, nav)
        }
        composable("placement/{id}", idArg) { PlacementScreen(it.arguments!!.getString("id")!!, nav) }
        composable("record/{id}", idArg) { RecordScreen(it.arguments!!.getString("id")!!, nav) }
    }
}

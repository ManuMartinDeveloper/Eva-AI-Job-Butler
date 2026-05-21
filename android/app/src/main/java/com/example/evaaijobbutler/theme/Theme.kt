package com.example.evaaijobbutler.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = AccentIndigo,
    secondary = AccentPurple,
    tertiary = AccentPink,
    background = DarkBgPrimary,
    surface = DarkBgSecondary,
    onPrimary = TextPrimary,
    onSecondary = TextPrimary,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    primaryContainer = DarkBgTertiary,
    onPrimaryContainer = TextPrimary
)

@Composable
fun EvaAIJobButlerTheme(
    darkTheme: Boolean = true, // Force Dark Mode for consistent premium branding
    dynamicColor: Boolean = false, // Disable dynamic colors to keep brand accents
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = Typography,
        content = content
    )
}

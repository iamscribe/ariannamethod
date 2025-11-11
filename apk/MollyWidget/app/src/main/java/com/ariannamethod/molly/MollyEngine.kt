package com.ariannamethod.molly

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader
import kotlin.math.min
import kotlin.random.Random

/**
 * Core engine for Molly's monologue
 * Handles reading from molly.md and weaving user phrases into the stream
 */
class MollyEngine(private val context: Context) {
    
    private val db = MollyDatabase(context)
    private var currentPosition = 0
    private var monologueText: String = ""
    private val displayLines = mutableListOf<String>()
    
    companion object {
        private const val LINES_TO_DISPLAY = 8
        private const val CHARS_PER_LINE = 100
    }
    
    init {
        loadMonologue()
    }
    
    /**
     * Load molly.md from assets or persistent storage
     */
    private fun loadMonologue() {
        // Try to load from persistent storage first (mutated version)
        val prefs = context.getSharedPreferences("molly_prefs", Context.MODE_PRIVATE)
        val savedMonologue = prefs.getString("monologue_text", null)
        val savedPosition = prefs.getInt("current_position", -1)
        
        if (savedMonologue != null && savedMonologue.isNotEmpty()) {
            monologueText = savedMonologue
            currentPosition = if (savedPosition >= 0) savedPosition else Random.nextInt(monologueText.length)
            return
        }
        
        // Load from assets (first time)
        try {
            val inputStream = context.assets.open("molly.md")
            monologueText = BufferedReader(InputStreamReader(inputStream)).use { it.readText() }
            
            // Remove markdown headers and clean up
            monologueText = monologueText
                .replace(Regex("^#.*$", RegexOption.MULTILINE), "")
                .replace(Regex("\\s+"), " ")
                .trim()
            
            // Start from random position
            currentPosition = if (monologueText.isNotEmpty()) {
                Random.nextInt(monologueText.length)
            } else 0
            
            // Save initial version
            saveMonologue()
            
        } catch (e: Exception) {
            monologueText = "..."
            currentPosition = 0
        }
    }
    
    /**
     * Save mutated monologue to persistent storage
     */
    private fun saveMonologue() {
        val prefs = context.getSharedPreferences("molly_prefs", Context.MODE_PRIVATE)
        prefs.edit()
            .putString("monologue_text", monologueText)
            .putInt("current_position", currentPosition)
            .apply()
    }
    
    /**
     * Get next chunk of monologue (called every 3 minutes or after user input)
     * Returns 5-6 lines for widget display
     */
    fun getNextChunk(): String {
        if (monologueText.isEmpty()) return "..."
        
        val chunkSize = CHARS_PER_LINE * LINES_TO_DISPLAY
        
        if (currentPosition >= monologueText.length) {
            currentPosition = 0
        }
        
        // Find word boundary at start
        var startPos = currentPosition
        while (startPos > 0 && monologueText[startPos - 1] != ' ' && monologueText[startPos - 1] != '\n') {
            startPos--
        }
        
        // Calculate end position
        var endPos = min(startPos + chunkSize, monologueText.length)
        
        // Find word boundary at end
        while (endPos < monologueText.length && monologueText[endPos] != ' ' && monologueText[endPos] != '\n') {
            endPos++
        }
        
        val chunk = monologueText.substring(startPos, endPos)
        currentPosition = endPos
        
        return chunk
    }
    
    /**
     * Weave user phrase into monologue based on metrics
     * This is the core of Molly's response mechanism
     * FIXED: Now uses resonance-based insertion like original molly.py
     */
    fun weavePhrase(userInput: String): String {
        if (userInput.isBlank()) return getNextChunk()
        
        // Split user input into fragments
        val fragments = MollyMetrics.splitFragments(userInput)
        if (fragments.isEmpty()) return getNextChunk()
        
        // Compute metrics for all fragments
        val fragmentsWithMetrics = fragments.map { fragment ->
            val metrics = MollyMetrics.computeMetrics(fragment)
            db.storeLine(fragment, metrics)
            Pair(fragment, metrics)
        }
        
        // Get next chunk
        val chunkSize = CHARS_PER_LINE * LINES_TO_DISPLAY
        
        if (currentPosition >= monologueText.length) {
            currentPosition = 0
        }
        
        // Find word boundary at start
        var startPos = currentPosition
        while (startPos > 0 && monologueText[startPos - 1] != ' ' && monologueText[startPos - 1] != '\n') {
            startPos--
        }
        
        // Calculate end position
        var endPos = min(startPos + chunkSize, monologueText.length)
        
        // Find word boundary at end
        while (endPos < monologueText.length && monologueText[endPos] != ' ' && monologueText[endPos] != '\n') {
            endPos++
        }
        
        var chunk = monologueText.substring(startPos, endPos)
        
        // Calculate max resonance for normalization
        val maxResonance = fragmentsWithMetrics.maxOfOrNull { it.second.resonance } ?: 1.0
        
        // Calculate insertion positions for ALL fragments based on resonance
        val inserts = mutableListOf<Pair<Int, String>>()
        fragmentsWithMetrics.forEachIndexed { i, (fragment, metrics) ->
            val baseRatio = (i + 1).toDouble() / (fragmentsWithMetrics.size + 1)
            val rNorm = if (maxResonance > 0) metrics.resonance / maxResonance else 0.0
            val ratio = baseRatio * (1 - rNorm) + 0.5 * rNorm
            var insertPos = (ratio * chunk.length).toInt().coerceIn(0, chunk.length)
            
            // Find nearest word boundary
            if (insertPos > 0 && insertPos < chunk.length) {
                // Look forward for space
                var forwardPos = insertPos
                while (forwardPos < chunk.length && chunk[forwardPos] != ' ' && chunk[forwardPos] != '\n') {
                    forwardPos++
                }
                // Look backward for space
                var backwardPos = insertPos
                while (backwardPos > 0 && chunk[backwardPos - 1] != ' ' && chunk[backwardPos - 1] != '\n') {
                    backwardPos--
                }
                // Choose closer boundary
                insertPos = if (forwardPos - insertPos <= insertPos - backwardPos) {
                    forwardPos
                } else {
                    backwardPos
                }
            }
            
            // Clean fragment (remove punctuation as in original Molly)
            val cleanFragment = fragment.replace(Regex("[^A-Za-z0-9\\s]"), "")
            inserts.add(Pair(insertPos, cleanFragment))
        }
        
        // Sort by position and insert all fragments
        inserts.sortBy { it.first }
        var offset = 0
        for ((pos, cleanFragment) in inserts) {
            val adjustedPos = (pos + offset).coerceIn(0, chunk.length)
            val before = chunk.substring(0, adjustedPos).trimEnd()
            val after = chunk.substring(adjustedPos).trimStart()
            chunk = before + (if (before.isNotEmpty()) " " else "") + 
                    cleanFragment + 
                    (if (after.isNotEmpty()) " " else "") + after
            offset += cleanFragment.length + 2
        }
        
        // MUTATE: Replace the chunk in monologueText permanently
        val beforeChunk = monologueText.substring(0, startPos)
        val afterChunk = if (endPos < monologueText.length) {
            monologueText.substring(endPos)
        } else ""
        monologueText = beforeChunk + chunk + afterChunk
        
        // Update position
        currentPosition = startPos + chunk.length
        
        // Save mutated monologue to persistent storage
        saveMonologue()
        
        return chunk
    }
    
    
    /**
     * Split chunk into display lines (~80 chars each)
     */
    private fun splitIntoLines(text: String): List<String> {
        val lines = mutableListOf<String>()
        val words = text.split(Regex("\\s+"))
        
        var currentLine = StringBuilder()
        for (word in words) {
            if (currentLine.length + word.length + 1 > CHARS_PER_LINE && currentLine.isNotEmpty()) {
                lines.add(currentLine.toString())
                currentLine = StringBuilder()
            }
            
            if (currentLine.isNotEmpty()) {
                currentLine.append(" ")
            }
            currentLine.append(word)
        }
        
        if (currentLine.isNotEmpty()) {
            lines.add(currentLine.toString())
        }
        
        // Return last LINES_TO_DISPLAY lines
        return lines.takeLast(LINES_TO_DISPLAY)
    }
    
    /**
     * Integrate with resonance.sqlite3 from ariannamethod ecosystem
     * This allows Molly to respond to system-wide events
     */
    fun integrateResonance(): String? {
        val resonanceLines = db.getResonanceLines(5)
        if (resonanceLines.isEmpty()) return null
        
        // Pick random line from resonance
        val line = resonanceLines.random()
        return weavePhrase(line)
    }
}

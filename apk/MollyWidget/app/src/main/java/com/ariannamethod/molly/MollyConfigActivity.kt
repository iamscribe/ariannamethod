package com.ariannamethod.molly

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.KeyEvent
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Configuration activity for user input
 * Opened when user taps the widget
 */
class MollyConfigActivity : Activity() {
    
    private var appWidgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Get widget ID
        appWidgetId = intent.getIntExtra(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        )
        
        // Setup minimal UI
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 16, 16, 16)
            setBackgroundColor(0xFFFFFFFF.toInt())
        }
        
        // Input field
        val input = EditText(this).apply {
            hint = ""
            textSize = 14f
            setTextColor(0xFF000000.toInt())
            setHintTextColor(0xFF888888.toInt())
            isSingleLine = true
            imeOptions = EditorInfo.IME_ACTION_SEND
            maxEms = 100
            
            val params = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            layoutParams = params
            
            setOnEditorActionListener { v, actionId, _ ->
                Log.d("MollyConfig", "onEditorAction: actionId=$actionId")
                if (actionId == EditorInfo.IME_ACTION_SEND) {
                    val userText = v.text.toString().trim().take(100)
                    Log.d("MollyConfig", "Submitting: $userText")
                    if (userText.isNotBlank()) {
                        submitInput(userText)
                    }
                    return@setOnEditorActionListener true
                }
                false
            }
        }
        
        layout.addView(input)
        
        setContentView(layout)
        
        // Focus input and show keyboard
        input.requestFocus()
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_VISIBLE)
    }
    
    private fun submitInput(text: String) {
        Log.d("MollyConfig", "submitInput called with: $text")
        // Send broadcast to widget with user input
        val intent = Intent(this, MollyWidget::class.java).apply {
            action = "com.ariannamethod.molly.ACTION_SUBMIT"
            putExtra("user_input", text)
        }
        sendBroadcast(intent)
        Log.d("MollyConfig", "Broadcast sent")
        
        // Set result and finish
        val resultValue = Intent().apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        setResult(RESULT_OK, resultValue)
        finish()
    }
    
    override fun onBackPressed() {
        // Cancel configuration
        setResult(RESULT_CANCELED)
        super.onBackPressed()
    }
}

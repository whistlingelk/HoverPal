/**
 * MainActivity.kt - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
 * Copyright (c) 2025 Daniel Theodore Seibert
 * Released under the MIT License.
 *
 * Short description:
 *   Demonstrates a Jetpack Compose-based Android Activity that manages kiosk-mode style
 *   functionality (connect, stream, record) by interfacing with a Pi server via WebSocket.
 *
 * How it works:
 *   • On create, sets up the UI with multiple states: idle, streaming, recording, etc.
 *   • Maintains a WebSocket connection to the Pi server.
 *   • The user toggles connect/stream/record with three vertical buttons,
 *     and color-coded states reflect success/failure or off/active.
 *   • On destroy or user exit, gracefully cleans up the connection.
 *
 * Dependencies:
 *   • Kotlin + Jetpack Compose for UI layout and state management.
 *   • OkHttp for WebSocket or a similar library.
 *   • Android OS version as set in Gradle (minSdk, targetSdk).
 *
 * Functions:
 *   • onCreate(savedInstanceState: Bundle?) - Entry point for the activity lifecycle.
 *   • toggleConnect() - Toggles between connect / disconnect with the server.
 *   • toggleStream() - Toggles camera streaming start / stop with the server.
 *   • toggleRecord() - Toggles recording start / stop with the server.
 *   • handleServerMessage(text: String) - Interprets server-sent text commands.
 *   • swapRedBlueChannels(bitmap: Bitmap): Bitmap - Example color-swap helper, if needed.
 */

package com.example.ws_test

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ws_test.ui.theme.Ws_testTheme
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString

/**
 * MainActivity is the primary Android entry point, showing a Jetpack Compose
 * screen with Connect, Stream, and Record toggles. It manages the WebSocket
 * connection lifecycle to a Pi server.
 */
class MainActivity : ComponentActivity() {

    private val okHttpClient by lazy {
        OkHttpClient.Builder().build()
    }

    // States
    private val connectState = mutableStateOf(ButtonState.Blue)
    private val streamState = mutableStateOf(ButtonState.Blue)
    private val recordState = mutableStateOf(ButtonState.Blue)

    private val statusMessage = mutableStateOf("Idle")
    private val errorMessage = mutableStateOf<String?>(null)

    private val currentFrame = mutableStateOf<androidx.compose.ui.graphics.ImageBitmap?>(null)
    private var webSocket: WebSocket? = null

    /**
     * onCreate sets up the composable UI and handles initial lifecycle tasks.
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            Ws_testTheme {
                Box(modifier = Modifier.fillMaxSize()) {
                    // Background video feed or black background
                    currentFrame.value?.let { frame ->
                        androidx.compose.foundation.Image(
                            bitmap = frame,
                            contentDescription = "Live stream",
                            modifier = Modifier.fillMaxSize()
                        )
                    } ?: Box(modifier = Modifier.fillMaxSize().background(Color.Black))

                    // Title
                    Text(
                        text = "HoverPal",
                        color = Color.White,
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .padding(top = 16.dp)
                    )

                    // Column of 3 vertical buttons on the right
                    Column(
                        modifier = Modifier
                            .align(Alignment.CenterEnd)
                            .padding(end = 20.dp)
                            .width(intrinsicSize = IntrinsicSize.Max),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // Connect button
                        Button(
                            onClick = { toggleConnect() },
                            enabled = true,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = buttonColor(connectState.value)
                            ),
                            modifier = Modifier.height(48.dp).fillMaxWidth()
                        ) {
                            Text(connectLabel(connectState.value))
                        }

                        // Stream button
                        val streamEnabled = (connectState.value == ButtonState.Green)
                        Button(
                            onClick = { toggleStream() },
                            enabled = streamEnabled,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = buttonColor(streamState.value)
                            ),
                            modifier = Modifier.height(48.dp).fillMaxWidth()
                        ) {
                            Text(streamLabel(streamState.value))
                        }

                        // Record button
                        val recordEnabled = (streamState.value == ButtonState.Green)
                        Button(
                            onClick = { toggleRecord() },
                            enabled = recordEnabled,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = buttonColor(recordState.value)
                            ),
                            modifier = Modifier.height(48.dp).fillMaxWidth()
                        ) {
                            Text(recordLabel(recordState.value))
                        }
                    }

                    // Error / status text
                    errorMessage.value?.let {
                        Text(
                            text = it,
                            color = Color.Red,
                            fontSize = 14.sp,
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .padding(8.dp)
                        )
                    }
                    Text(
                        text = statusMessage.value,
                        color = Color.Gray,
                        fontSize = 14.sp,
                        modifier = Modifier
                            .align(Alignment.BottomStart)
                            .padding(8.dp)
                    )
                }
            }
        }
    }

    /**
     * toggleConnect checks the connectState, toggles connect/disconnect via WebSocket.
     */
    private fun toggleConnect() {
        when (connectState.value) {
            ButtonState.Blue, ButtonState.Red -> doConnect()
            ButtonState.Green -> doDisconnect()
        }
    }

    /**
     * toggleStream toggles streaming start/stop with the Pi server.
     */
    private fun toggleStream() {
        when (streamState.value) {
            ButtonState.Blue, ButtonState.Red -> doStartStream()
            ButtonState.Green -> doStopStream()
        }
    }

    /**
     * toggleRecord toggles record start/stop with the Pi server.
     */
    private fun toggleRecord() {
        when (recordState.value) {
            ButtonState.Blue, ButtonState.Red -> doStartRecord()
            ButtonState.Green -> doStopRecord()
        }
    }

    /**
     * doConnect attempts to open a WebSocket, sets connectState to Green if successful.
     */
    private fun doConnect() {
        statusMessage.value = "Connecting..."
        errorMessage.value = null
        connectState.value = ButtonState.Blue
        streamState.value = ButtonState.Blue
        recordState.value = ButtonState.Blue
        currentFrame.value = null

        val request = Request.Builder().url("ws://192.168.86.250:5000/").build()
        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: okhttp3.Response) {
                this@MainActivity.webSocket = webSocket
                runOnUiThread {
                    connectState.value = ButtonState.Green
                    statusMessage.value = "Connected"
                }
                webSocket.send("START_LINK")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                runOnUiThread {
                    handleServerMessage(text)
                }
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                // Possibly the camera frames
                val bmp = decodeFrame(bytes.toByteArray())
                runOnUiThread {
                    currentFrame.value = bmp
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                runOnUiThread {
                    connectState.value = ButtonState.Red
                    statusMessage.value = "Connection Failed"
                    errorMessage.value = "Connect error: ${t.message}"
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(code, reason)
                runOnUiThread {
                    handleForcedDisconnect()
                }
            }
        }
        webSocket = okHttpClient.newWebSocket(request, listener)
    }

    /**
     * doDisconnect closes the WebSocket, resetting all states.
     */
    private fun doDisconnect() {
        // If streaming is active, forcibly stop first
        if (streamState.value == ButtonState.Green) {
            doStopStream(force = true)
        }
        webSocket?.send("STOP_LINK")
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        connectState.value = ButtonState.Blue
        streamState.value = ButtonState.Blue
        recordState.value = ButtonState.Blue
        currentFrame.value = null
        statusMessage.value = "Disconnected"
        errorMessage.value = null
    }

    /**
     * handleForcedDisconnect forcibly sets connectState to Red, stopping stream/record states too.
     */
    private fun handleForcedDisconnect() {
        connectState.value = ButtonState.Red
        streamState.value = ButtonState.Blue
        recordState.value = ButtonState.Blue
        currentFrame.value = null
        statusMessage.value = "Disconnected by server"
    }

    /**
     * doStartStream sends START_STREAM to the server and updates states.
     */
    private fun doStartStream() {
        if (webSocket == null) {
            streamState.value = ButtonState.Red
            errorMessage.value = "Can't start stream; not connected!"
            return
        }
        webSocket?.send("START_STREAM")
        statusMessage.value = "Requesting stream..."
    }

    /**
     * doStopStream optionally stops record, then sends STOP_STREAM to the server.
     */
    private fun doStopStream(force: Boolean = false) {
        if (recordState.value == ButtonState.Green) {
            doStopRecord(force = true)
        }
        if (webSocket == null) {
            streamState.value = ButtonState.Red
            errorMessage.value = "Can't stop stream; not connected!"
            return
        }
        webSocket?.send("STOP_STREAM")
        if (force) {
            streamState.value = ButtonState.Blue
            statusMessage.value = "Stream forcibly stopped"
        }
    }

    /**
     * doStartRecord sends START_RECORD if connected/streaming.
     */
    private fun doStartRecord() {
        if (webSocket == null) {
            recordState.value = ButtonState.Red
            errorMessage.value = "Can't start record; not connected!"
            return
        }
        webSocket?.send("START_RECORD")
        statusMessage.value = "Requesting record..."
    }

    /**
     * doStopRecord stops recording if active, sending STOP_RECORD.
     */
    private fun doStopRecord(force: Boolean = false) {
        if (webSocket == null) {
            recordState.value = ButtonState.Red
            errorMessage.value = "Can't stop record; not connected!"
            return
        }
        webSocket?.send("STOP_RECORD")
        if (force) {
            recordState.value = ButtonState.Blue
            statusMessage.value = "Record forcibly stopped"
        }
    }

    /**
     * handleServerMessage handles text from the server (RECORD_STARTED, etc.) to update UI states.
     */
    private fun handleServerMessage(text: String) {
        when (text) {
            "STREAM_STARTED" -> {
                streamState.value = ButtonState.Green
                statusMessage.value = "Stream On"
            }
            "STREAM_STOPPED" -> {
                streamState.value = ButtonState.Blue
                recordState.value = ButtonState.Blue
                statusMessage.value = "Stream Off"
            }
            "RECORD_STARTED" -> {
                recordState.value = ButtonState.Green
                statusMessage.value = "Record On"
            }
            "RECORD_STOPPED" -> {
                recordState.value = ButtonState.Blue
                statusMessage.value = "Record Off"
            }
            else -> Log.d("MainActivity", "Unknown server msg: $text")
        }
    }

    /**
     * decodeFrame decodes the raw JPEG bytes, optionally swapping color channels if needed.
     */
    private fun decodeFrame(bytes: ByteArray): androidx.compose.ui.graphics.ImageBitmap? {
        // If your frames are BGR-tinted, fix them here
        val bmp = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        bmp ?: return null
        // Optionally do swapRedBlueChannels(bmp) before converting
        return swapRedBlueChannels(bmp).asImageBitmap()
    }

    /**
     * swapRedBlueChannels is an optional method to channel-swap a Bitmap in place if needed.
     */
    private fun swapRedBlueChannels(bmp: android.graphics.Bitmap): android.graphics.Bitmap {
        val out = bmp.copy(android.graphics.Bitmap.Config.ARGB_8888, true)
        val w = out.width
        val h = out.height
        val pixels = IntArray(w * h)
        out.getPixels(pixels, 0, w, 0, 0, w, h)
        for (i in pixels.indices) {
            val c = pixels[i]
            val alpha = (c shr 24) and 0xFF
            val red   = (c shr 16) and 0xFF
            val green = (c shr 8)  and 0xFF
            val blue  = c and 0xFF
            // swap R <-> B
            val newColor = (alpha shl 24) or (blue shl 16) or (green shl 8) or (red)
            pixels[i] = newColor
        }
        out.setPixels(pixels, 0, w, 0, 0, w, h)
        return out
    }

    /**
     * buttonColor maps ButtonState to a Compose Color for the container.
     */
    private fun buttonColor(state: ButtonState): Color {
        return when (state) {
            ButtonState.Blue -> Color.Blue
            ButtonState.Green -> Color.Green
            ButtonState.Red -> Color.Red
        }
    }

    /**
     * connectLabel, streamLabel, recordLabel provide text for each button based on ButtonState.
     */
    private fun connectLabel(state: ButtonState): String =
        when (state) {
            ButtonState.Blue -> "CONNECT"
            ButtonState.Green -> "DISCONNECT"
            ButtonState.Red -> "RETRY CONNECT"
        }

    private fun streamLabel(state: ButtonState): String =
        when (state) {
            ButtonState.Blue -> "START STREAM"
            ButtonState.Green -> "STOP STREAM"
            ButtonState.Red -> "RETRY STREAM"
        }

    private fun recordLabel(state: ButtonState): String =
        when (state) {
            ButtonState.Blue -> "START RECORD"
            ButtonState.Green -> "STOP RECORD"
            ButtonState.Red -> "RETRY RECORD"
        }
}

/**
 * A simple enum representing each button's color-coded state.
 */
enum class ButtonState {
    Blue,  // idle/off
    Green, // active
    Red    // error/failure
}

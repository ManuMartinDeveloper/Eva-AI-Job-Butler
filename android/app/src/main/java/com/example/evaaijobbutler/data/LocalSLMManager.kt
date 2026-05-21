package com.example.evaaijobbutler.data

import android.util.Log
import com.google.ai.client.generativeai.GenerativeModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

@Serializable
data class ChatMessage(val role: String, val content: String)

class LocalSLMManager(
    private var provider: String = "ollama",
    private var modelName: String = "phi4",
    private var hostAddress: String = "http://10.0.2.2:11434",
    private var geminiApiKey: String = ""
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true }

    fun updateSettings(provider: String, modelName: String, hostAddress: String, geminiApiKey: String) {
        this.provider = provider
        this.modelName = modelName
        this.hostAddress = hostAddress
        this.geminiApiKey = geminiApiKey
    }

    suspend fun generateResponse(prompt: String, systemPrompt: String = ""): String {
        return generateChatResponse(listOf(ChatMessage("user", prompt)), systemPrompt)
    }

    suspend fun generateChatResponse(history: List<ChatMessage>, systemPrompt: String = ""): String = withContext(Dispatchers.IO) {
        when (provider.lowercase()) {
            "gemini" -> {
                if (geminiApiKey.isEmpty()) {
                    return@withContext "Error: Gemini API Key is empty. Please set it in Settings."
                }
                try {
                    val generativeModel = GenerativeModel(
                        modelName = modelName.ifEmpty { "gemini-1.5-flash" },
                        apiKey = geminiApiKey
                    )
                    // If systemPrompt is set, prepend it to the conversation or configure it in generative model
                    val fullPrompt = if (systemPrompt.isNotEmpty()) "$systemPrompt\n\n" else ""
                    val response = generativeModel.generateContent(
                        fullPrompt + history.joinToString("\n") { "${it.role}: ${it.content}" }
                    )
                    return@withContext response.text ?: "No response from Gemini API"
                } catch (e: Exception) {
                    Log.e("LocalSLMManager", "Gemini error", e)
                    return@withContext "Gemini API Error: ${e.localizedMessage}"
                }
            }
            "ollama" -> {
                val url = "$hostAddress/api/chat"
                try {
                    val requestBody = buildJsonObject {
                        put("model", modelName.ifEmpty { "phi4" })
                        put("stream", false)
                        putJsonArray("messages") {
                            if (systemPrompt.isNotEmpty()) {
                                addJsonObject {
                                    put("role", "system")
                                    put("content", systemPrompt)
                                }
                            }
                            history.forEach { msg ->
                                addJsonObject {
                                    put("role", msg.role)
                                    put("content", msg.content)
                                }
                            }
                        }
                    }.toString()

                    val body = requestBody.toRequestBody("application/json".toMediaType())
                    val request = Request.Builder()
                        .url(url)
                        .post(body)
                        .build()

                    client.newCall(request).execute().use { response ->
                        if (!response.isSuccessful) {
                            return@withContext "Ollama Error: HTTP ${response.code} ${response.message}"
                        }
                        val responseBody = response.body?.string() ?: return@withContext "Empty response from Ollama"
                        val jsonElement = json.parseToJsonElement(responseBody)
                        val assistantMsg = jsonElement.jsonObject["message"]?.jsonObject
                        return@withContext assistantMsg?.get("content")?.jsonPrimitive?.content 
                            ?: "Ollama parsed message content was null. Raw response: $responseBody"
                    }
                } catch (e: IOException) {
                    Log.e("LocalSLMManager", "Ollama connection failed", e)
                    return@withContext "Ollama connection failed. Ensure Ollama is running at $hostAddress and model '$modelName' is downloaded."
                } catch (e: Exception) {
                    Log.e("LocalSLMManager", "Ollama error", e)
                    return@withContext "Ollama Error: ${e.localizedMessage}"
                }
            }
            else -> {
                return@withContext "Error: Unknown provider '$provider'. Select Ollama or Gemini."
            }
        }
    }

    suspend fun checkConnection(): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        if (provider.lowercase() == "gemini") {
            if (geminiApiKey.isEmpty()) return@withContext Pair(false, "Gemini API Key is empty")
            return@withContext Pair(true, "Gemini selected (Cloud)")
        }
        
        val url = "$hostAddress/api/tags"
        val request = Request.Builder().url(url).build()
        try {
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: ""
                    return@withContext Pair(true, "Connected! Models available: " + parseModelsList(body))
                }
                return@withContext Pair(false, "HTTP ${response.code} connecting to Ollama")
            }
        } catch (e: Exception) {
            return@withContext Pair(false, "Cannot reach Ollama at $hostAddress: ${e.localizedMessage}")
        }
    }

    private fun parseModelsList(jsonString: String): String {
        return try {
            val jsonElement = json.parseToJsonElement(jsonString)
            val modelsArray = jsonElement.jsonObject["models"]?.jsonArray
            val modelNames = modelsArray?.mapNotNull { 
                it.jsonObject["name"]?.jsonPrimitive?.content 
            }
            modelNames?.joinToString(", ") ?: "None"
        } catch (e: Exception) {
            "Connected (Failed to parse models list)"
        }
    }
}

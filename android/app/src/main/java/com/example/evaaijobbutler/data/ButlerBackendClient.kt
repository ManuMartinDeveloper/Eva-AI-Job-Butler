package com.example.evaaijobbutler.data

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

@Serializable
data class JobLead(
    val id: Int,
    val title: String,
    val company: String,
    val location: String? = null,
    val description: String? = null,
    val site: String? = null,
    val is_applied: Boolean = false
)

@Serializable
data class AgentStatus(
    val is_running: Boolean,
    val next_run_time: String? = null
)

@Serializable
data class ScoutRequest(
    val search_term: String,
    val location: String,
    val limit: Int
)

class ButlerBackendClient(
    private var backendUrl: String = "http://10.0.2.2:8000"
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true }

    fun updateBackendUrl(url: String) {
        this.backendUrl = url
    }

    suspend fun getJobs(): List<JobLead> = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$backendUrl/api/jobs/")
            .build()
        try {
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext emptyList()
                val bodyStr = response.body?.string() ?: return@withContext emptyList()
                return@withContext json.decodeFromString<List<JobLead>>(bodyStr)
            }
        } catch (e: Exception) {
            Log.e("ButlerBackendClient", "Failed to fetch jobs", e)
            return@withContext emptyList()
        }
    }

    suspend fun getAgentStatus(): AgentStatus? = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$backendUrl/api/agent/status")
            .build()
        try {
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext null
                val bodyStr = response.body?.string() ?: return@withContext null
                return@withContext json.decodeFromString<AgentStatus>(bodyStr)
            }
        } catch (e: Exception) {
            Log.e("ButlerBackendClient", "Failed to fetch agent status", e)
            return@withContext null
        }
    }

    suspend fun startAgent(): Boolean = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$backendUrl/api/agent/start")
            .post("".toRequestBody("application/json".toMediaType()))
            .build()
        try {
            client.newCall(request).execute().use { response ->
                return@withContext response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("ButlerBackendClient", "Failed to start agent", e)
            return@withContext false
        }
    }

    suspend fun stopAgent(): Boolean = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$backendUrl/api/agent/stop")
            .post("".toRequestBody("application/json".toMediaType()))
            .build()
        try {
            client.newCall(request).execute().use { response ->
                return@withContext response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("ButlerBackendClient", "Failed to stop agent", e)
            return@withContext false
        }
    }

    suspend fun triggerScout(searchTerm: String, location: String, limit: Int): Boolean = withContext(Dispatchers.IO) {
        val payload = json.encodeToString(ScoutRequest.serializer(), ScoutRequest(searchTerm, location, limit))
        val body = payload.toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url("$backendUrl/api/jobs/scout")
            .post(body)
            .build()
        try {
            client.newCall(request).execute().use { response ->
                return@withContext response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("ButlerBackendClient", "Failed to trigger scout", e)
            return@withContext false
        }
    }

    suspend fun checkBackendConnection(): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url(backendUrl)
            .build()
        try {
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    return@withContext Pair(true, "Connected! Server online.")
                }
                return@withContext Pair(false, "HTTP ${response.code} from server")
            }
        } catch (e: Exception) {
            return@withContext Pair(false, "Connection failed: ${e.localizedMessage}")
        }
    }
}

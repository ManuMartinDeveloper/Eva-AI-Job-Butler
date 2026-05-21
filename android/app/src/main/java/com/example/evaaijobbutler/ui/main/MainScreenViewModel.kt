package com.example.evaaijobbutler.ui.main

import android.app.Application
import android.content.Context
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.evaaijobbutler.data.ButlerBackendClient
import com.example.evaaijobbutler.data.ChatMessage
import com.example.evaaijobbutler.data.JobLead
import com.example.evaaijobbutler.data.LocalSLMManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainScreenViewModel(application: Application) : AndroidViewModel(application) {

    private val prefs = application.getSharedPreferences("eva_butler_prefs", Context.MODE_PRIVATE)

    // Configuration Settings (Persistent)
    private val _provider = MutableStateFlow(prefs.getString("provider", "ollama") ?: "ollama")
    val provider = _provider.asStateFlow()

    private val _modelName = MutableStateFlow(prefs.getString("model_name", "phi4") ?: "phi4")
    val modelName = _modelName.asStateFlow()

    private val _ollamaHost = MutableStateFlow(prefs.getString("ollama_host", "http://10.0.2.2:11434") ?: "http://10.0.2.2:11434")
    val ollamaHost = _ollamaHost.asStateFlow()

    private val _backendUrl = MutableStateFlow(prefs.getString("backend_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000")
    val backendUrl = _backendUrl.asStateFlow()

    private val _geminiApiKey = MutableStateFlow(prefs.getString("gemini_key", "") ?: "")
    val geminiApiKey = _geminiApiKey.asStateFlow()

    // Service Clients
    private val slmManager = LocalSLMManager(
        provider = _provider.value,
        modelName = _modelName.value,
        hostAddress = _ollamaHost.value,
        geminiApiKey = _geminiApiKey.value
    )

    private val backendClient = ButlerBackendClient(
        backendUrl = _backendUrl.value
    )

    // UI States
    private val _jobs = MutableStateFlow<List<JobLead>>(emptyList())
    val jobs = _jobs.asStateFlow()

    private val _agentRunning = MutableStateFlow(false)
    val agentRunning = _agentRunning.asStateFlow()

    private val _nextAgentRun = MutableStateFlow<String?>(null)
    val nextAgentRun = _nextAgentRun.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading = _isLoading.asStateFlow()

    private val _selectedJob = MutableStateFlow<JobLead?>(null)
    val selectedJob = _selectedJob.asStateFlow()

    // Connections Statuses
    private val _backendConnected = MutableStateFlow(false)
    val backendConnected = _backendConnected.asStateFlow()

    private val _backendConnMsg = MutableStateFlow("Unchecked")
    val backendConnMsg = _backendConnMsg.asStateFlow()

    private val _slmConnected = MutableStateFlow(false)
    val slmConnected = _slmConnected.asStateFlow()

    private val _slmConnMsg = MutableStateFlow("Unchecked")
    val slmConnMsg = _slmConnMsg.asStateFlow()

    // Chat states
    private val _chatMessages = MutableStateFlow<List<ChatMessage>>(listOf(
        ChatMessage("assistant", "Hello! I am your local AI Butler Advisor. Select a job lead, and I will help you tailor your pitch or prepare for the interview using your local LLM context.")
    ))
    val chatMessages = _chatMessages.asStateFlow()

    private val _chatLoading = MutableStateFlow(false)
    val chatLoading = _chatLoading.asStateFlow()

    init {
        refreshDashboard()
        testConnections()
    }

    fun updateSettings(
        newProvider: String,
        newModelName: String,
        newOllamaHost: String,
        newBackendUrl: String,
        newGeminiApiKey: String
    ) {
        _provider.value = newProvider
        _modelName.value = newModelName
        _ollamaHost.value = newOllamaHost
        _backendUrl.value = newBackendUrl
        _geminiApiKey.value = newGeminiApiKey

        prefs.edit().apply {
            putString("provider", newProvider)
            putString("model_name", newModelName)
            putString("ollama_host", newOllamaHost)
            putString("backend_url", newBackendUrl)
            putString("gemini_key", newGeminiApiKey)
            apply()
        }

        slmManager.updateSettings(newProvider, newModelName, newOllamaHost, newGeminiApiKey)
        backendClient.updateBackendUrl(newBackendUrl)

        testConnections()
        refreshDashboard()
    }

    fun refreshDashboard() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                // Fetch job leads
                val jobsList = backendClient.getJobs()
                _jobs.value = jobsList

                // Fetch agent scheduler status
                backendClient.getAgentStatus()?.let { status ->
                    _agentRunning.value = status.is_running
                    _nextAgentRun.value = status.next_run_time
                }
            } catch (e: Exception) {
                Log.e("MainScreenViewModel", "Error refreshing dashboard data", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun testConnections() {
        viewModelScope.launch {
            // Check FastAPI
            val (beOk, beMsg) = backendClient.checkBackendConnection()
            _backendConnected.value = beOk
            _backendConnMsg.value = beMsg

            // Check Ollama/Gemini
            val (slmOk, slmMsg) = slmManager.checkConnection()
            _slmConnected.value = slmOk
            _slmConnMsg.value = slmMsg
        }
    }

    fun selectJob(job: JobLead?) {
        _selectedJob.value = job
    }

    fun triggerScout(searchTerm: String, location: String, limit: Int) {
        viewModelScope.launch {
            _isLoading.value = true
            val success = backendClient.triggerScout(searchTerm, location, limit)
            if (success) {
                // Refresh list shortly after triggering
                kotlinx.coroutines.delay(5000)
                refreshDashboard()
            }
            _isLoading.value = false
        }
    }

    fun toggleAgent(start: Boolean) {
        viewModelScope.launch {
            val success = if (start) backendClient.startAgent() else backendClient.stopAgent()
            if (success) {
                _agentRunning.value = start
                refreshDashboard()
            }
        }
    }

    fun sendChatMessage(messageContent: String) {
        if (messageContent.trim().isEmpty() || _chatLoading.value) return

        val userMsg = ChatMessage("user", messageContent)
        _chatMessages.value = _chatMessages.value + userMsg
        _chatLoading.value = true

        viewModelScope.launch {
            try {
                // Prepare context
                val jobContext = _selectedJob.value
                val systemPrompt = buildString {
                    append("You are Eva AI Job Butler's local advisor. ")
                    append("You are helping the user (Manu) prepare for a job application or interview. ")
                    if (jobContext != null) {
                        append("\nSelected Job Context:\n")
                        append("Title: ${jobContext.title}\n")
                        append("Company: ${jobContext.company}\n")
                        append("Location: ${jobContext.location ?: "N/A"}\n")
                        append("Description: ${jobContext.description ?: "N/A"}\n")
                    }
                    append("\nBe direct, technical, encouraging, and format your answers with markdown bullet points if appropriate.")
                }

                val reply = slmManager.generateChatResponse(_chatMessages.value, systemPrompt)
                _chatMessages.value = _chatMessages.value + ChatMessage("assistant", reply)
            } catch (e: Exception) {
                _chatMessages.value = _chatMessages.value + ChatMessage("assistant", "Error talking to SLM: ${e.localizedMessage}")
            } finally {
                _chatLoading.value = false
            }
        }
    }

    fun clearChat() {
        _chatMessages.value = listOf(
            ChatMessage("assistant", "Chat cleared. Ask me anything to get started with interview prep!")
        )
    }
}

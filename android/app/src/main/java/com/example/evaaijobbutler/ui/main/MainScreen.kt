package com.example.evaaijobbutler.ui.main

import android.app.Application
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.evaaijobbutler.data.ChatMessage
import com.example.evaaijobbutler.data.JobLead
import com.example.evaaijobbutler.theme.*

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val viewModel: MainScreenViewModel = viewModel {
        MainScreenViewModel(context.applicationContext as Application)
    }

    var activeTab by remember { mutableStateOf("dashboard") }

    Scaffold(
        bottomBar = {
            BottomNavigationBar(
                currentTab = activeTab,
                onTabSelected = { activeTab = it }
            )
        },
        containerColor = DarkBgPrimary
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0x0F6366F1), Color.Transparent),
                        radius = 1200f
                    )
                )
        ) {
            when (activeTab) {
                "dashboard" -> DashboardTab(viewModel)
                "jobs" -> JobLeadsTab(viewModel, onSwitchToChat = { activeTab = "chat" })
                "chat" -> SLMAdvisorChatTab(viewModel)
                "settings" -> SettingsTab(viewModel)
            }
        }
    }
}

// ==========================================
// BOTTOM NAVIGATION BAR
// ==========================================
@Composable
fun BottomNavigationBar(currentTab: String, onTabSelected: (String) -> Unit) {
    NavigationBar(
        containerColor = DarkBgSecondary,
        tonalElevation = 8.dp,
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp))
            .clip(RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp))
    ) {
        NavigationBarItem(
            selected = currentTab == "dashboard",
            onClick = { onTabSelected("dashboard") },
            icon = { Icon(Icons.Default.Home, contentDescription = "Dashboard") },
            label = { Text("Dashboard") },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentIndigo,
                selectedTextColor = AccentIndigo,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary,
                indicatorColor = Color(0x1F6366F1)
            )
        )
        NavigationBarItem(
            selected = currentTab == "jobs",
            onClick = { onTabSelected("jobs") },
            icon = { Icon(Icons.Default.Search, contentDescription = "Jobs") },
            label = { Text("Scout Leads") },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentIndigo,
                selectedTextColor = AccentIndigo,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary,
                indicatorColor = Color(0x1F6366F1)
            )
        )
        NavigationBarItem(
            selected = currentTab == "chat",
            onClick = { onTabSelected("chat") },
            icon = { Icon(Icons.Default.PlayArrow, contentDescription = "Advisor") },
            label = { Text("SLM Advisor") },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentIndigo,
                selectedTextColor = AccentIndigo,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary,
                indicatorColor = Color(0x1F6366F1)
            )
        )
        NavigationBarItem(
            selected = currentTab == "settings",
            onClick = { onTabSelected("settings") },
            icon = { Icon(Icons.Default.Settings, contentDescription = "Settings") },
            label = { Text("Settings") },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentIndigo,
                selectedTextColor = AccentIndigo,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary,
                indicatorColor = Color(0x1F6366F1)
            )
        )
    }
}

// ==========================================
// 1. DASHBOARD TAB
// ==========================================
@Composable
fun DashboardTab(viewModel: MainScreenViewModel) {
    val jobs by viewModel.jobs.collectAsState()
    val agentRunning by viewModel.agentRunning.collectAsState()
    val backendConnected by viewModel.backendConnected.collectAsState()
    val backendMsg by viewModel.backendConnMsg.collectAsState()
    val slmConnected by viewModel.slmConnected.collectAsState()
    val slmMsg by viewModel.slmConnMsg.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "🤖 Eva AI Job Butler",
                        color = TextPrimary,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Mobile Control Panel",
                        color = TextSecondary,
                        fontSize = 14.sp
                    )
                }
                IconButton(onClick = { viewModel.refreshDashboard(); viewModel.testConnections() }) {
                    Icon(
                        Icons.Default.Refresh,
                        contentDescription = "Refresh",
                        tint = if (isLoading) AccentIndigo else TextSecondary
                    )
                }
            }
        }

        // Connection status card row
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, CardBorder, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = CardBackground)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Connection Status",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(bottom = 12.dp)
                    )
                    
                    // FastAPI Status
                    StatusItemRow(
                        title = "FastAPI Backend Connection",
                        status = if (backendConnected) "ONLINE" else "OFFLINE",
                        color = if (backendConnected) AccentEmerald else AccentRose,
                        detail = backendMsg
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    HorizontalDivider(color = Color(0x0F6366F1))
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // SLM Status
                    StatusItemRow(
                        title = "Local SLM Brain Status",
                        status = if (slmConnected) "CONNECTED" else "DISCONNECTED",
                        color = if (slmConnected) AccentPurple else AccentRose,
                        detail = slmMsg
                    )
                }
            }
        }

        // Stats Matrix Cards
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Total scouted jobs
                Card(
                    modifier = Modifier
                        .weight(1f)
                        .border(1.dp, CardBorder, RoundedCornerShape(16.dp)),
                    colors = CardDefaults.cardColors(containerColor = CardBackground)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Scouted Leads", color = TextSecondary, fontSize = 12.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "${jobs.size}",
                            color = TextPrimary,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // Scheduler State
                Card(
                    modifier = Modifier
                        .weight(1f)
                        .border(1.dp, CardBorder, RoundedCornerShape(16.dp)),
                    colors = CardDefaults.cardColors(containerColor = CardBackground)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Agent Scheduler", color = TextSecondary, fontSize = 12.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(10.dp)
                                    .clip(RoundedCornerShape(5.dp))
                                    .background(if (agentRunning) AccentEmerald else AccentRose)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = if (agentRunning) "RUNNING" else "STOPPED",
                                color = TextPrimary,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }

        // Agent Scheduler Controller
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, CardBorder, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = CardBackground)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Agent Controller",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "The background scheduling agent automatically wakes up to scrape, ingest documents, and tailors drafts on a 4-hour cycle.",
                        color = TextSecondary,
                        fontSize = 13.sp
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { viewModel.toggleAgent(!agentRunning) },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (agentRunning) AccentRose else AccentIndigo
                        ),
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(
                            imageVector = if (agentRunning) Icons.Default.Close else Icons.Default.PlayArrow,
                            contentDescription = null
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(if (agentRunning) "Stop Background Scheduler" else "Start Background Scheduler")
                    }
                }
            }
        }
    }
}

@Composable
fun StatusItemRow(title: String, status: String, color: Color, detail: String) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(title, color = TextSecondary, fontSize = 14.sp, fontWeight = FontWeight.Medium)
            Surface(
                color = color.copy(alpha = 0.15f),
                shape = RoundedCornerShape(6.dp),
                border = BorderStroke(1.dp, color.copy(alpha = 0.3f))
            ) {
                Text(
                    text = status,
                    color = color,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                )
            }
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = detail,
            color = TextMuted,
            fontSize = 12.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

// ==========================================
// 2. JOB LEADS TAB
// ==========================================
@Composable
fun JobLeadsTab(viewModel: MainScreenViewModel, onSwitchToChat: () -> Unit) {
    val jobs by viewModel.jobs.collectAsState()
    val selectedJob by viewModel.selectedJob.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    var searchTerm by remember { mutableStateOf("AI Engineer") }
    var locationSearch by remember { mutableStateOf("Bengaluru") }
    var scrapeLimit by remember { mutableStateOf("10") }
    var showScoutDialog by remember { mutableStateOf(false) }

    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "🕵️ Scouted Job Leads",
                        color = TextPrimary,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Tailor profile & chat with SLM",
                        color = TextSecondary,
                        fontSize = 14.sp
                    )
                }
                Button(
                    onClick = { showScoutDialog = true },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentIndigo),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Icon(Icons.Default.Add, contentDescription = "Scout")
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Scout")
                }
            }

            if (isLoading && jobs.isEmpty()) {
                Box(modifier = Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = AccentIndigo)
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(jobs) { job ->
                        JobLeadCard(
                            job = job,
                            isSelected = selectedJob?.id == job.id,
                            onSelect = { viewModel.selectJob(job) }
                        )
                    }
                    if (jobs.isEmpty()) {
                        item {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 40.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text("No jobs scouted yet. Tap Scout to run a scraper.", color = TextSecondary)
                            }
                        }
                    }
                }
            }
        }

        // Job Detail Dialog overlay
        selectedJob?.let { job ->
            AlertDialog(
                onDismissRequest = { viewModel.selectJob(null) },
                title = { Text(job.title, color = TextPrimary, fontWeight = FontWeight.Bold) },
                text = {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 300.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        Text(job.company, color = AccentIndigo, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                        Text(job.location ?: "Location N/A", color = TextSecondary, fontSize = 13.sp)
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = job.description ?: "No description scraped.",
                            color = TextPrimary,
                            fontSize = 14.sp
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            viewModel.selectJob(job) // lock selected context in VM
                            onSwitchToChat()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = AccentEmerald)
                    ) {
                        Icon(Icons.Default.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Tailor & Advisor Chat")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { viewModel.selectJob(null) }) {
                        Text("Close", color = TextSecondary)
                    }
                },
                containerColor = DarkBgSecondary,
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.border(1.dp, CardBorder, RoundedCornerShape(16.dp))
            )
        }

        // Search trigger Dialog
        if (showScoutDialog) {
            AlertDialog(
                onDismissRequest = { showScoutDialog = false },
                title = { Text("Launch Scraper Scout", color = TextPrimary) },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedTextField(
                            value = searchTerm,
                            onValueChange = { searchTerm = it },
                            label = { Text("Search Job Title") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AccentIndigo,
                                unfocusedBorderColor = TextSecondary,
                                focusedLabelColor = AccentIndigo
                            )
                        )
                        OutlinedTextField(
                            value = locationSearch,
                            onValueChange = { locationSearch = it },
                            label = { Text("Location") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AccentIndigo,
                                unfocusedBorderColor = TextSecondary,
                                focusedLabelColor = AccentIndigo
                            )
                        )
                        OutlinedTextField(
                            value = scrapeLimit,
                            onValueChange = { scrapeLimit = it },
                            label = { Text("Limit (max 50)") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AccentIndigo,
                                unfocusedBorderColor = TextSecondary,
                                focusedLabelColor = AccentIndigo
                            )
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            val limit = scrapeLimit.toIntOrNull() ?: 10
                            viewModel.triggerScout(searchTerm, locationSearch, limit)
                            showScoutDialog = false
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = AccentIndigo)
                    ) {
                        Text("Launch Scout")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showScoutDialog = false }) {
                        Text("Cancel", color = TextSecondary)
                    }
                },
                containerColor = DarkBgSecondary,
                shape = RoundedCornerShape(16.dp)
            )
        }
    }
}

@Composable
fun JobLeadCard(job: JobLead, isSelected: Boolean, onSelect: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onSelect() }
            .border(
                1.dp,
                if (isSelected) AccentIndigo else CardBorder,
                RoundedCornerShape(14.dp)
            ),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) Color(0x1F6366F1) else CardBackground
        )
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = job.title,
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = job.company,
                        color = AccentIndigo,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
                Surface(
                    color = Color(0x0F6366F1),
                    shape = RoundedCornerShape(6.dp),
                    border = BorderStroke(1.dp, CardBorder)
                ) {
                    Text(
                        text = job.site ?: "Indeed",
                        color = AccentPurple,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = job.location ?: "N/A",
                    color = TextSecondary,
                    fontSize = 12.sp
                )
                Text(
                    text = if (job.is_applied) "Applied" else "Lead Open",
                    color = if (job.is_applied) AccentEmerald else TextSecondary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

// ==========================================
// 3. SLM ADVISOR CHAT TAB
// ==========================================
@Composable
fun SLMAdvisorChatTab(viewModel: MainScreenViewModel) {
    val chatMessages by viewModel.chatMessages.collectAsState()
    val chatLoading by viewModel.chatLoading.collectAsState()
    val selectedJob by viewModel.selectedJob.collectAsState()

    var textInput by remember { mutableStateOf("") }
    val lazyListState = rememberLazyListState()

    // Scroll to bottom on updates
    LaunchedEffect(chatMessages.size) {
        if (chatMessages.isNotEmpty()) {
            lazyListState.animateScrollToItem(chatMessages.size - 1)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "🎤 SLM Advisor Chat",
            color = TextPrimary,
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold
        )
        
        // Context indicator
        AnimatedVisibility(
            visible = selectedJob != null,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            selectedJob?.let { job ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                        .background(Color(0x1510B981), RoundedCornerShape(8.dp))
                        .border(1.dp, AccentEmerald.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(modifier = Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Info, contentDescription = null, tint = AccentEmerald, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Tailoring context: ${job.title} at ${job.company}",
                            color = AccentEmerald,
                            fontSize = 12.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Clear",
                        tint = AccentRose,
                        modifier = Modifier
                            .size(18.dp)
                            .clickable { viewModel.selectJob(null) }
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Chat conversation bubble list
        LazyColumn(
            state = lazyListState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(Color(0x33000000), RoundedCornerShape(16.dp))
                .border(1.dp, CardBorder, RoundedCornerShape(16.dp))
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(chatMessages) { msg ->
                ChatBubbleRow(msg = msg)
            }
            if (chatLoading) {
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Start
                    ) {
                        Surface(
                            color = CardBackground,
                            shape = RoundedCornerShape(18.dp, 18.dp, 18.dp, 4.dp),
                            border = BorderStroke(1.dp, CardBorder)
                        ) {
                            Text(
                                text = "Thinking...",
                                color = TextSecondary,
                                fontSize = 14.sp,
                                modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp)
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Input bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { viewModel.clearChat() }) {
                Icon(Icons.Default.Delete, contentDescription = "Clear Chat", tint = AccentRose)
            }
            OutlinedTextField(
                value = textInput,
                onValueChange = { textInput = it },
                placeholder = { Text("Ask local model or request resume tailoring...") },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary,
                    focusedContainerColor = DarkBgSecondary,
                    unfocusedContainerColor = DarkBgSecondary,
                    focusedBorderColor = AccentIndigo,
                    unfocusedBorderColor = CardBorder
                ),
                shape = RoundedCornerShape(24.dp),
                modifier = Modifier.weight(1f)
            )
            IconButton(
                onClick = {
                    if (textInput.trim().isNotEmpty()) {
                        viewModel.sendChatMessage(textInput)
                        textInput = ""
                    }
                },
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        Brush.linearGradient(listOf(AccentIndigo, AccentPurple)),
                        RoundedCornerShape(24.dp)
                    )
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send", tint = Color.White)
            }
        }
    }
}

@Composable
fun ChatBubbleRow(msg: ChatMessage) {
    val isUser = msg.role == "user"
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            color = if (isUser) AccentIndigo else CardBackground,
            shape = if (isUser) RoundedCornerShape(18.dp, 18.dp, 4.dp, 18.dp) else RoundedCornerShape(18.dp, 18.dp, 18.dp, 4.dp),
            border = if (isUser) null else BorderStroke(1.dp, CardBorder),
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Text(
                text = msg.content,
                color = TextPrimary,
                fontSize = 14.sp,
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp)
            )
        }
    }
}

// ==========================================
// 4. SETTINGS TAB
// ==========================================
@Composable
fun SettingsTab(viewModel: MainScreenViewModel) {
    val currentProvider by viewModel.provider.collectAsState()
    val currentModelName by viewModel.modelName.collectAsState()
    val currentOllamaHost by viewModel.ollamaHost.collectAsState()
    val currentBackendUrl by viewModel.backendUrl.collectAsState()
    val currentGeminiApiKey by viewModel.geminiApiKey.collectAsState()

    var provider by remember { mutableStateOf(currentProvider) }
    var modelName by remember { mutableStateOf(currentModelName) }
    var ollamaHost by remember { mutableStateOf(currentOllamaHost) }
    var backendUrl by remember { mutableStateOf(currentBackendUrl) }
    var geminiApiKey by remember { mutableStateOf(currentGeminiApiKey) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Text(
                text = "⚙️ Connection Settings",
                color = TextPrimary,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold
            )
        }

        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, CardBorder, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = CardBackground)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Text(
                        text = "AI Brain Configuration",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold
                    )

                    // Provider Toggle Selection
                    Column {
                        Text("Inference Provider", color = TextSecondary, fontSize = 13.sp)
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Button(
                                onClick = {
                                    provider = "ollama"
                                    modelName = "phi4"
                                },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (provider == "ollama") AccentIndigo else CardBackground
                                ),
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Ollama Local")
                            }
                            Button(
                                onClick = {
                                    provider = "gemini"
                                    modelName = "gemini-1.5-flash"
                                },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (provider == "gemini") AccentIndigo else CardBackground
                                ),
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Gemini Cloud")
                            }
                        }
                    }

                    // Model Name Input
                    OutlinedTextField(
                        value = modelName,
                        onValueChange = { modelName = it },
                        label = { Text("Model Name") },
                        colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = AccentIndigo),
                        modifier = Modifier.fillMaxWidth()
                    )

                    // Conditional Gemini API Key input
                    if (provider == "gemini") {
                        OutlinedTextField(
                            value = geminiApiKey,
                            onValueChange = { geminiApiKey = it },
                            label = { Text("Gemini API Key") },
                            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = AccentIndigo),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    // Ollama Host Address input
                    if (provider == "ollama") {
                        OutlinedTextField(
                            value = ollamaHost,
                            onValueChange = { ollamaHost = it },
                            label = { Text("Ollama Endpoint") },
                            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = AccentIndigo),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    Spacer(modifier = Modifier.height(6.dp))
                    HorizontalDivider(color = Color(0x0F6366F1))
                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "FastAPI Backend Connection",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold
                    )

                    OutlinedTextField(
                        value = backendUrl,
                        onValueChange = { backendUrl = it },
                        label = { Text("Backend Base URL") },
                        colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = AccentIndigo),
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = {
                            viewModel.updateSettings(
                                provider,
                                modelName,
                                ollamaHost,
                                backendUrl,
                                geminiApiKey
                            )
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = AccentEmerald),
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.Check, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Save and Apply Settings")
                    }
                }
            }
        }
    }
}

// Simple composable states
@Composable
fun rememberScrollState() = androidx.compose.foundation.rememberScrollState()

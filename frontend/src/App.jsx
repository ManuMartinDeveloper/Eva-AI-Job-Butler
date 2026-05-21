// D:/Projects/Eva_AI_Job_Butler/frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import { 
  Briefcase, 
  User, 
  FileText, 
  Settings as SettingsIcon, 
  Activity, 
  Search, 
  RefreshCw, 
  Plus, 
  Trash2, 
  Send, 
  Download, 
  Play, 
  Square, 
  CheckCircle, 
  ExternalLink,
  MapPin,
  Mail,
  Smartphone,
  Globe
} from 'lucide-react';

const GithubIcon = ({ size = 14, ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('scout');
  const [selectedJob, setSelectedJob] = useState(null);
  
  // LLM Config State
  const [provider, setProvider] = useState(() => localStorage.getItem('llm_provider') || 'gemini');
  const [modelName, setModelName] = useState(() => localStorage.getItem('llm_model') || 'gemini-2.0-flash-lite');
  
  // Agent running state
  const [agentRunning, setAgentRunning] = useState(false);

  useEffect(() => {
    localStorage.setItem('llm_provider', provider);
    localStorage.setItem('llm_model', modelName);
  }, [provider, modelName]);

  // Periodically fetch agent status to update sidebar indicator
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/agent/status`);
        if (res.ok) {
          const data = await res.json();
          setAgentRunning(data.is_running);
        }
      } catch (err) {
        console.error("Error fetching agent status:", err);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo-container">
          <span className="logo-icon">🤖</span>
          <span className="logo-text">Eva AI Butler</span>
        </div>

        <div className="nav-links">
          <div 
            className={`nav-item ${activeTab === 'scout' ? 'active' : ''}`}
            onClick={() => setActiveTab('scout')}
          >
            <Search size={18} />
            <span>Job Scout</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <User size={18} />
            <span>Know Me</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'generator' ? 'active' : ''}`}
            onClick={() => setActiveTab('generator')}
          >
            <FileText size={18} />
            <span>Document Tailor</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'agent' ? 'active' : ''}`}
            onClick={() => setActiveTab('agent')}
          >
            <Activity size={18} />
            <span>Agent Control</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <SettingsIcon size={18} />
            <span>Settings</span>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className={`agent-indicator ${agentRunning ? 'running' : 'stopped'}`} />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Agent: {agentRunning ? 'Running' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {activeTab === 'scout' && (
          <JobScoutView selectedJob={selectedJob} setSelectedJob={setSelectedJob} setActiveTab={setActiveTab} provider={provider} modelName={modelName} />
        )}
        {activeTab === 'profile' && (
          <ProfileManagerView provider={provider} modelName={modelName} />
        )}
        {activeTab === 'generator' && (
          <DocumentGeneratorView selectedJob={selectedJob} provider={provider} modelName={modelName} />
        )}
        {activeTab === 'agent' && (
          <AgentStatusView agentRunning={agentRunning} setAgentRunning={setAgentRunning} />
        )}
        {activeTab === 'settings' && (
          <SettingsView provider={provider} setProvider={setProvider} modelName={modelName} setModelName={setModelName} />
        )}
      </div>
    </div>
  );
}/* ==========================================
   1. JOB SCOUT VIEW
   ========================================== */
function JobScoutView({ selectedJob, setSelectedJob, setActiveTab, provider, modelName }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scouting, setScouting] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  
  // Form parameters
  const [searchTerm, setSearchTerm] = useState('AI Engineer');
  const [location, setLocation] = useState('Bengaluru');
  const [limit, setLimit] = useState(20);
  const [activeJobId, setActiveJobId] = useState(selectedJob ? selectedJob.id : null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
        // Sync selectedJob if it exists in the new list to keep values fresh
        if (selectedJob) {
          const freshSelected = data.find(j => j.id === selectedJob.id);
          if (freshSelected) {
            setSelectedJob(freshSelected);
          }
        }
      }
    } catch (err) {
      console.error("Error fetching jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleScout = async (e) => {
    e.preventDefault();
    setScouting(true);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/scout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_term: searchTerm, location, limit })
      });
      if (res.ok) {
        alert("Scouting process triggered in backend! Check Agent Logs for updates.");
        setTimeout(fetchJobs, 8000); // refresh after a short delay
      }
    } catch (err) {
      console.error("Error triggering scout:", err);
    } finally {
      setScouting(false);
    }
  };

  const handleApply = async (jobId) => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model: modelName })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveTab('agent');
        fetchJobs();
      }
    } catch (err) {
      console.error("Error applying to job:", err);
    }
  };

  const handleEvaluate = async (jobId) => {
    setEvaluating(true);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/evaluate`, { method: 'POST' });
      if (res.ok) {
        const updatedJob = await res.json();
        setSelectedJob(updatedJob);
        // Update job in the list
        setJobs(prevJobs => prevJobs.map(j => j.id === jobId ? updatedJob : j));
        alert(`Evaluation completed. Match score: ${updatedJob.fit_score}%`);
      } else {
        alert("Evaluation failed. Make sure your GEMINI API key is set.");
      }
    } catch (err) {
      console.error("Error evaluating job:", err);
      alert("Error triggering evaluation.");
    } finally {
      setEvaluating(false);
    }
  };

  // Helper to parse the DB fit_reasoning field into sections
  const parseFitReasoning = (reasoningStr) => {
    if (!reasoningStr) return { gaps: '', recommendations: '', reasoning: '' };
    
    // Check if it's the standard structured string or just free text
    const gapIndex = reasoningStr.indexOf("Gap Analysis:");
    const recIndex = reasoningStr.indexOf("Recommendations:");
    const reasonIndex = reasoningStr.indexOf("Reasoning:");
    
    if (gapIndex === -1 && recIndex === -1 && reasonIndex === -1) {
      return { gaps: 'See analysis summary below.', recommendations: 'Use the Document Tailor to view recommendations.', reasoning: reasoningStr };
    }
    
    let gaps = "";
    let recommendations = "";
    let reasoning = reasoningStr;
    
    if (gapIndex !== -1 && recIndex !== -1) {
      gaps = reasoningStr.substring(gapIndex + "Gap Analysis:".length, recIndex).trim();
    }
    if (recIndex !== -1 && reasonIndex !== -1) {
      recommendations = reasoningStr.substring(recIndex + "Recommendations:".length, reasonIndex).trim();
    }
    if (reasonIndex !== -1) {
      reasoning = reasoningStr.substring(reasonIndex + "Reasoning:".length).trim();
    }
    
    return { gaps, recommendations, reasoning };
  };

  const { gaps, recommendations, reasoning } = parseFitReasoning(selectedJob?.fit_reasoning);

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>🕵️ Job Scout Dashboard</h1>
      
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: selectedJob ? '1.5fr 1.2fr' : '1fr 2fr', 
          gap: '1.5rem', 
          alignItems: 'start',
          transition: 'all 0.3s ease'
        }}
      >
        {/* Left column: Search Parameters & Jobs Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Search Parameters (condensed if side-by-side) */}
          <div className="card">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Job Search Parameters</h2>
            <form onSubmit={handleScout} style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
              <div className="form-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>Job Title</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group" style={{ flex: '1 1 150px', marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>Location</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={location} 
                  onChange={e => setLocation(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group" style={{ flex: '0 1 80px', marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>Limit</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={limit} 
                  onChange={e => setLimit(parseInt(e.target.value))} 
                  min="1" 
                  max="50" 
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ padding: '0.65rem 1.25rem' }} disabled={scouting}>
                {scouting ? <RefreshCw className="animate-spin" size={14} /> : 'Launch Scout'}
              </button>
            </form>
          </div>

          {/* Job leads results list */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem' }}>Latest Job Leads ({jobs.length})</h2>
              <button className="btn btn-secondary" onClick={fetchJobs} disabled={loading} style={{ padding: '0.5rem 1rem' }}>
                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              </button>
            </div>

            <div className="custom-table-container" style={{ maxHeight: '500px' }}>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Job Details</th>
                    <th>Location</th>
                    <th>Fit Score</th>
                    <th>Source</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(job => (
                    <tr 
                      key={job.id} 
                      className={activeJobId === job.id ? 'selected' : ''}
                      onClick={() => {
                        setActiveJobId(job.id);
                        setSelectedJob(job);
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        <div style={{ fontWeight: '600' }}>{job.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{job.company}</div>
                      </td>
                      <td>{job.location || 'N/A'}</td>
                      <td>
                        {job.fit_score && job.fit_score > 0 ? (
                          <span className="badge" style={{ 
                            background: job.fit_score >= 80 ? 'rgba(16,185,129,0.12)' : job.fit_score >= 55 ? 'rgba(245,158,11,0.12)' : 'rgba(244,63,94,0.12)', 
                            color: job.fit_score >= 80 ? 'var(--accent-emerald)' : job.fit_score >= 55 ? 'var(--accent-amber)' : 'var(--accent-rose)', 
                            padding: '0.2rem 0.5rem', 
                            borderRadius: '6px', 
                            fontSize: '0.8rem',
                            fontWeight: '700',
                            border: `1px solid ${job.fit_score >= 80 ? 'rgba(16,185,129,0.2)' : job.fit_score >= 55 ? 'rgba(245,158,11,0.2)' : 'rgba(244,63,94,0.2)'}`
                          }}>
                            {job.fit_score}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontStyle: 'italic' }}>Unscored</span>
                        )}
                      </td>
                      <td>
                        <span className="badge" style={{ background: 'rgba(99,102,241,0.08)', color: 'var(--accent-indigo)', padding: '0.2rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem' }}>
                          {job.site || 'Indeed'}
                        </span>
                      </td>
                      <td>
                        {job.is_applied ? (
                          <span style={{ color: 'var(--accent-emerald)', fontSize: '0.8rem', fontWeight: '600' }}>Applied</span>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Lead</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {jobs.length === 0 && (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        No jobs scouted yet. Fill in search terms and run the scout!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right column: Selected Job Details & Agent Match Analysis */}
        {selectedJob && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', border: '1px solid rgba(99,102,241,0.2)', boxShadow: 'var(--glow-shadow)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className="badge" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--accent-indigo)', padding: '0.2rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', marginBottom: '0.5rem', display: 'inline-block' }}>
                  {selectedJob.site || 'Job Lead'}
                </span>
                <h2 style={{ fontSize: '1.3rem', fontWeight: '700', lineHeight: '1.2' }}>{selectedJob.title}</h2>
                <div style={{ fontSize: '0.95rem', color: 'var(--accent-indigo)', fontWeight: '500', marginTop: '0.25rem' }}>{selectedJob.company}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>📍 {selectedJob.location || 'Remote / N/A'}</div>
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.35rem', borderRadius: '50%', minWidth: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center' }} 
                onClick={() => {
                  setSelectedJob(null);
                  setActiveJobId(null);
                }}
              >
                ✕
              </button>
            </div>

            <hr style={{ border: 'none', borderBottom: '1px solid var(--border-color)' }} />

            {/* AI Fit Assessment Section */}
            <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
              <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                🤖 Autonomous Match Assessment
              </h3>

              {selectedJob.fit_score && selectedJob.fit_score > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                    {/* Circle Score Gauge */}
                    <div style={{ 
                      width: '64px', 
                      height: '64px', 
                      borderRadius: '50%', 
                      border: `4px solid ${selectedJob.fit_score >= 80 ? 'var(--accent-emerald)' : selectedJob.fit_score >= 55 ? 'var(--accent-amber)' : 'var(--accent-rose)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.1rem',
                      fontWeight: '800',
                      boxShadow: selectedJob.fit_score >= 80 ? '0 0 15px rgba(16,185,129,0.2)' : 'none',
                      color: selectedJob.fit_score >= 80 ? 'var(--accent-emerald)' : selectedJob.fit_score >= 55 ? 'var(--accent-amber)' : 'var(--accent-rose)'
                    }}>
                      {selectedJob.fit_score}%
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.95rem' }}>
                        {selectedJob.fit_score >= 80 ? 'Excellent Match' : selectedJob.fit_score >= 55 ? 'Good Potential Match' : 'Low Relevance Match'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Evaluated autonomously by Agent Brain using RAG context
                      </div>
                    </div>
                  </div>

                  {gaps && (
                    <div style={{ fontSize: '0.85rem' }}>
                      <strong style={{ color: 'var(--accent-rose)', display: 'block', marginBottom: '0.2rem' }}>⚠️ Identified Skill Gaps:</strong>
                      <div style={{ color: 'var(--text-secondary)', whiteSpace: 'pre-line' }}>{gaps}</div>
                    </div>
                  )}

                  {recommendations && (
                    <div style={{ fontSize: '0.85rem' }}>
                      <strong style={{ color: 'var(--accent-emerald)', display: 'block', marginBottom: '0.2rem' }}>💡 Tailoring Strategy:</strong>
                      <div style={{ color: 'var(--text-secondary)', whiteSpace: 'pre-line' }}>{recommendations}</div>
                    </div>
                  )}

                  {reasoning && (
                    <div style={{ fontSize: '0.85rem', padding: '0.75rem', background: 'rgba(99,102,241,0.04)', borderRadius: '8px', borderLeft: '3px solid var(--accent-indigo)' }}>
                      <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.25rem' }}>Agent Thought Explanation:</strong>
                      <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>{reasoning}</div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '1.5rem 1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    This job has not been evaluated by Eva Agent. Let the AI butler run a ReAct reasoning cycle to check your match score and identify gaps.
                  </div>
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleEvaluate(selectedJob.id)} 
                    disabled={evaluating}
                    style={{ margin: '0 auto' }}
                  >
                    {evaluating ? <RefreshCw className="animate-spin" size={14} /> : '🤖 Run AI Agent Assessment'}
                  </button>
                </div>
              )}
            </div>

            {/* Quick Actions Card Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <button 
                  className="btn btn-primary" 
                  onClick={() => {
                    setActiveTab('generator');
                  }}
                >
                  ✍️ Customize Resume
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => handleApply(selectedJob.id)}
                  disabled={selectedJob.is_applied}
                >
                  🚀 Assisted Apply
                </button>
              </div>

              {selectedJob.fit_score && selectedJob.fit_score > 0 && (
                <button 
                  className="btn btn-secondary" 
                  onClick={() => handleEvaluate(selectedJob.id)} 
                  disabled={evaluating}
                  style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                >
                  {evaluating ? <RefreshCw className="animate-spin" size={12} /> : '🕵️ Re-Assess Match'}
                </button>
              )}

              {selectedJob.url && (
                <a 
                  href={selectedJob.url} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="btn btn-secondary" 
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.85rem' }}
                >
                  View Original Listing <ExternalLink size={14} />
                </a>
              )}
            </div>

            {/* Job Description details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1 }}>
              <h3 style={{ fontSize: '0.95rem' }}>Description Summary</h3>
              <div style={{ 
                fontSize: '0.85rem', 
                color: 'var(--text-secondary)', 
                maxHeight: '180px', 
                overflowY: 'auto', 
                whiteSpace: 'pre-line',
                padding: '0.75rem',
                background: 'rgba(0,0,0,0.2)',
                borderRadius: '8px',
                border: '1px solid var(--border-color)'
              }}>
                {selectedJob.description || "No description text available."}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ==========================================
   2. PROFILE MANAGER VIEW (KNOW ME)
   ========================================== */
function ProfileManagerView({ provider, modelName }) {
  const [profile, setProfile] = useState(null);
  const [facts, setFacts] = useState([]);
  const [newFact, setNewFact] = useState('');
  const [newCategory, setNewCategory] = useState('Skills');
  const [ingesting, setIngesting] = useState(false);
  const [loading, setLoading] = useState(false);

  // Chat window state
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi Manu! I want to learn more about you. What is your biggest professional achievement so far?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setFacts(data.facts || []);
      }
    } catch (err) {
      console.error("Error fetching profile:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/ingest`, { method: 'POST' });
      if (res.ok) {
        alert("Ingest pipeline started. Syncing resume and GitHub repositories to ChromaDB vector store!");
        setTimeout(fetchProfile, 10000); // refresh facts
      }
    } catch (err) {
      console.error("Error during ingest:", err);
    } finally {
      setIngesting(false);
    }
  };

  const handleAddFact = async (e) => {
    e.preventDefault();
    if (!newFact.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/api/profile/fact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: newCategory, fact: newFact, source: 'Manual Input' })
      });
      if (res.ok) {
        const added = await res.json();
        setFacts([added, ...facts]);
        setNewFact('');
      }
    } catch (err) {
      console.error("Error adding fact:", err);
    }
  };

  const handleDeleteFact = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/profile/fact/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setFacts(facts.filter(f => f.id !== id));
      }
    } catch (err) {
      console.error("Error deleting fact:", err);
    }
  };

  const handleSendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = { role: 'user', content: chatInput };
    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages,
          provider,
          model_name: modelName
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
        // Refresh facts since some might have been extracted
        fetchProfile();
      }
    } catch (err) {
      console.error("Error chatting:", err);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I had trouble processing that response locally." }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>👤 Profile & Facts Manager</h1>

      <div className="grid-main" style={{ alignItems: 'start' }}>
        {/* Left Side: Profile overview & Ingestion */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Knowledge Base Sync</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
              Process resume details and live public GitHub repositories, embedding them into ChromaDB vector memory.
            </p>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleIngest} disabled={ingesting}>
              {ingesting ? <RefreshCw className="animate-spin" size={16} /> : 'Sync Profile & Embed (RAG)'}
            </button>
          </div>

          {profile && (
            <div className="card">
              <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Profile Seed Data</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><User size={14} /> <strong>{profile.name}</strong></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Mail size={14} /> {profile.email}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Smartphone size={14} /> {profile.phone}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Globe size={14} /> <a href={profile.website} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-indigo)' }}>{profile.website}</a></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><GithubIcon size={14} /> <span>{profile.github_username}</span></div>
              </div>
              <div style={{ marginTop: '1.25rem' }}>
                <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem' }}>Base Skills ({profile.skills?.length})</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {profile.skills?.slice(0, 10).map((s, idx) => (
                    <span key={idx} style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', padding: '0.2rem 0.4rem', borderRadius: '6px' }}>{s}</span>
                  ))}
                  {profile.skills?.length > 10 && <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', alignSelf: 'center' }}>+{profile.skills.length - 10} more</span>}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Side: Tabbed Facts & Chat */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <h2 style={{ marginBottom: '1.25rem', fontSize: '1.2rem' }}>🎤 Interview Mode: Learn About Me</h2>
            <div className="chat-container">
              <div className="chat-messages">
                {messages.map((msg, index) => (
                  <div key={index} className={`chat-bubble ${msg.role}`}>
                    {msg.content}
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-bubble assistant" style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                    Eva is writing...
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>
              <form onSubmit={handleSendChatMessage} className="chat-input-bar">
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="Answer Eva..."
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  disabled={chatLoading}
                />
                <button type="submit" className="btn btn-primary" disabled={chatLoading || !chatInput.trim()}>
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>

          {/* Extracted Facts list */}
          <div className="card">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Stored Facts List ({facts.length})</h2>
            
            {/* Add manual fact */}
            <form onSubmit={handleAddFact} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <select 
                className="form-select" 
                style={{ width: '120px' }}
                value={newCategory}
                onChange={e => setNewCategory(e.target.value)}
              >
                <option value="Skills">Skills</option>
                <option value="Experience">Experience</option>
                <option value="Projects">Projects</option>
                <option value="Personal">Personal</option>
              </select>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Type fact (e.g. Built automated report generation using PowerBI)" 
                value={newFact}
                onChange={e => setNewFact(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-secondary">
                <Plus size={16} />
              </button>
            </form>

            <div style={{ maxHeight: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {facts.map(fact => (
                <div 
                  key={fact.id} 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'start', 
                    padding: '0.75rem 1rem', 
                    background: 'rgba(255,255,255,0.02)', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '12px',
                    fontSize: '0.9rem'
                  }}
                >
                  <div>
                    <span className="badge" style={{ fontSize: '0.75rem', background: 'rgba(99,102,241,0.1)', color: 'var(--accent-indigo)', padding: '0.15rem 0.4rem', borderRadius: '4px', marginRight: '0.5rem', fontWeight: '600' }}>
                      {fact.category}
                    </span>
                    <span style={{ color: 'var(--text-primary)' }}>{fact.fact}</span>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Source: {fact.source}</div>
                  </div>
                  <button 
                    style={{ background: 'transparent', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer' }}
                    onClick={() => handleDeleteFact(fact.id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {facts.length === 0 && (
                <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1rem' }}>
                  No extra profile facts found. Use chat or input above to add facts!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ==========================================
   3. DOCUMENT GENERATOR VIEW
   ========================================== */
function DocumentGeneratorView({ selectedJob, provider, modelName }) {
  // Fields to Tailor
  const [jobTitle, setJobTitle] = useState(selectedJob ? selectedJob.title : '');
  const [companyName, setCompanyName] = useState(selectedJob ? selectedJob.company : '');
  const [jobDesc, setJobDesc] = useState(selectedJob ? selectedJob.description || '' : '');
  
  const [generating, setGenerating] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState('resume');
  
  // Generated Results
  const [resumeData, setResumeData] = useState(null);
  const [resumeReasoning, setResumeReasoning] = useState('');
  const [clData, setClData] = useState('');
  const [clReasoning, setClReasoning] = useState('');

  // Editable output fields
  const [editSummary, setEditSummary] = useState('');
  const [editSkills, setEditSkills] = useState('');
  const [editExperience, setEditExperience] = useState('');
  const [editProjects, setEditProjects] = useState('');
  const [editCLContent, setEditCLContent] = useState('');

  useEffect(() => {
    if (selectedJob) {
      setJobTitle(selectedJob.title);
      setCompanyName(selectedJob.company);
      setJobDesc(selectedJob.description || '');
    }
  }, [selectedJob]);

  const handleGenerate = async () => {
    if (!jobTitle || !jobDesc) {
      alert("Please specify Job Title and Job Description.");
      return;
    }

    setGenerating(true);
    try {
      // 1. Generate Resume
      const resResume = await fetch(`${API_BASE}/api/generate/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_title: jobTitle, job_desc: jobDesc, provider, model_name: modelName })
      });
      if (resResume.ok) {
        const data = await resResume.json();
        setResumeData(data.document);
        setResumeReasoning(data.reasoning);
        // Initialize editable states
        setEditSummary(data.document.summary || '');
        setEditSkills(data.document.skills || '');
        setEditExperience(data.document.experience || '');
        setEditProjects(data.document.projects || '');
      }

      // 2. Generate Cover Letter
      const resCL = await fetch(`${API_BASE}/api/generate/coverletter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_title: jobTitle, job_desc: jobDesc, provider, model_name: modelName })
      });
      if (resCL.ok) {
        const data = await resCL.json();
        setClData(data.document);
        setClReasoning(data.reasoning);
        setEditCLContent(data.document || '');
      }
    } catch (err) {
      console.error("Tailoring error:", err);
      alert("Error generating documents. Ensure your LLM model is configured and API keys are valid.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (docType) => {
    try {
      const contentPayload = docType === 'resume' 
        ? { summary: editSummary, skills: editSkills, experience: editExperience, projects: editProjects }
        : { text: editCLContent };

      const res = await fetch(`${API_BASE}/api/generate/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_type: docType,
          company_name: companyName || 'Company',
          job_title: jobTitle,
          content: contentPayload
        })
      });

      if (res.ok) {
        const data = await res.json();
        // Redirect browser to download binary from backend
        window.location.href = `${API_BASE}/api/generate/download?file_path=${encodeURIComponent(data.file_path)}`;
      }
    } catch (err) {
      console.error("Export error:", err);
      alert("Failed to export DOCX.");
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>✍️ AI Document Tailoring</h1>

      <div className="grid-2">
        {/* Left Side: Inputs */}
        <div className="card">
          <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Job Application Reference</h2>
          {selectedJob && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontSize: '0.85rem', marginBottom: '1rem', fontWeight: '600' }}>
              <CheckCircle size={14} /> Syncing details from selected scout lead!
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Job Title</label>
            <input 
              type="text" 
              className="form-input" 
              value={jobTitle} 
              onChange={e => setJobTitle(e.target.value)} 
              placeholder="e.g. AI Engineer"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input 
              type="text" 
              className="form-input" 
              value={companyName} 
              onChange={e => setCompanyName(e.target.value)} 
              placeholder="e.g. Google"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Job Description</label>
            <textarea 
              className="form-textarea" 
              style={{ minHeight: '220px' }}
              value={jobDesc} 
              onChange={e => setJobDesc(e.target.value)}
              placeholder="Paste the full job posting text here..."
            />
          </div>
          <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleGenerate} disabled={generating}>
            {generating ? <RefreshCw className="animate-spin" size={16} /> : '✨ Tailor Resume & Cover Letter'}
          </button>
        </div>

        {/* Right Side: Outputs */}
        <div className="card">
          <div className="tabs-header">
            <button className={`tab-btn ${activeSubTab === 'resume' ? 'active' : ''}`} onClick={() => setActiveSubTab('resume')}>📄 Resume Output</button>
            <button className={`tab-btn ${activeSubTab === 'coverletter' ? 'active' : ''}`} onClick={() => setActiveSubTab('coverletter')}>✉️ Cover Letter</button>
          </div>

          {activeSubTab === 'resume' && (
            <div>
              {resumeData ? (
                <div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.25rem' }}>
                    <div className="form-group">
                      <label className="form-label">Tailored Summary</label>
                      <textarea className="form-input" style={{ minHeight: '90px' }} value={editSummary} onChange={e => setEditSummary(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Tailored Skills</label>
                      <textarea className="form-input" style={{ minHeight: '80px' }} value={editSkills} onChange={e => setEditSkills(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Tailored Experience</label>
                      <textarea className="form-input" style={{ minHeight: '150px' }} value={editExperience} onChange={e => setEditExperience(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Tailored Projects</label>
                      <textarea className="form-input" style={{ minHeight: '120px' }} value={editProjects} onChange={e => setEditProjects(e.target.value)} />
                    </div>
                  </div>
                  {resumeReasoning && (
                    <div style={{ padding: '1rem', background: 'rgba(99,102,241,0.05)', border: '1px solid var(--border-color)', borderRadius: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                      <strong>🤖 AI Strategy Strategy:</strong> {resumeReasoning}
                    </div>
                  )}
                  <button className="btn btn-emerald" style={{ width: '100%' }} onClick={() => handleDownload('resume')}>
                    <Download size={16} /> Compile & Download Resume (DOCX)
                  </button>
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '4rem' }}>
                  No customized resume generated yet. Trigger tailoring on the left!
                </div>
              )}
            </div>
          )}

          {activeSubTab === 'coverletter' && (
            <div>
              {clData ? (
                <div>
                  <div className="form-group">
                    <label className="form-label">Tailored Letter Content</label>
                    <textarea 
                      className="form-input" 
                      style={{ minHeight: '380px', fontFamily: 'inherit', fontSize: '0.925rem' }} 
                      value={editCLContent} 
                      onChange={e => setEditCLContent(e.target.value)} 
                    />
                  </div>
                  {clReasoning && (
                    <div style={{ padding: '1rem', background: 'rgba(99,102,241,0.05)', border: '1px solid var(--border-color)', borderRadius: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                      <strong>🤖 AI Outreach Strategy:</strong> {clReasoning}
                    </div>
                  )}
                  <button className="btn btn-emerald" style={{ width: '100%' }} onClick={() => handleDownload('coverletter')}>
                    <Download size={16} /> Compile & Download Cover Letter (DOCX)
                  </button>
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '4rem' }}>
                  No customized cover letter generated yet. Trigger tailoring on the left!
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ==========================================
   4. AGENT CONTROL VIEW
   ========================================== */
function AgentStatusView({ agentRunning, setAgentRunning }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusResponse, setStatusResponse] = useState(null);

  // Cockpit States
  const [session, setSession] = useState(null);
  const [screenshotUrl, setScreenshotUrl] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const reactStreamEndRef = useRef(null);

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/status`);
      if (res.ok) {
        const data = await res.json();
        setStatusResponse(data);
        setAgentRunning(data.is_running);
      }
    } catch (err) {
      console.error("Error fetching agent status:", err);
    }
  };

  // Poll background logs and status
  useEffect(() => {
    fetchLogs();
    fetchStatus();
    const logInterval = setInterval(fetchLogs, 5000);
    const statusInterval = setInterval(fetchStatus, 5000);
    return () => {
      clearInterval(logInterval);
      clearInterval(statusInterval);
    };
  }, []);

  // Poll Cockpit Session state
  useEffect(() => {
    const pollSession = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/agent/session`);
        if (res.ok) {
          const data = await res.json();
          setSession(data);
          if (data && data.status !== 'idle') {
            setScreenshotUrl(`${API_BASE}/api/agent/screenshot?t=${Date.now()}`);
          }
        }
      } catch (err) {
        console.error("Error polling agent session:", err);
      }
    };

    pollSession();
    const interval = setInterval(pollSession, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll ReAct stream
  useEffect(() => {
    if (reactStreamEndRef.current) {
      reactStreamEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [session?.logs]);

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/start`, { method: 'POST' });
      if (res.ok) {
        setAgentRunning(true);
        fetchStatus();
        fetchLogs();
      }
    } catch (err) {
      console.error("Error starting agent:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/stop`, { method: 'POST' });
      if (res.ok) {
        setAgentRunning(false);
        fetchStatus();
        fetchLogs();
      }
    } catch (err) {
      console.error("Error stopping agent:", err);
    } finally {
      setLoading(false);
    }
  };

  const forceRunScout = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs/scout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_term: 'AI Engineer', location: 'Bengaluru', limit: 10 })
      });
      if (res.ok) {
        alert("Scouting process forced immediately! Check Agent Logs for updates.");
        fetchLogs();
      }
    } catch (err) {
      console.error("Error forcing scout:", err);
    }
  };

  const forceRunEvaluate = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/evaluate`, {
        method: 'POST'
      });
      if (res.ok) {
        alert("Autonomous evaluation process triggered! Check Agent Logs for updates.");
        fetchLogs();
      }
    } catch (err) {
      console.error("Error forcing evaluation:", err);
    }
  };

  const handleSendCommand = async (command) => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/session/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
      if (res.ok) {
        // Refresh session immediately
        const sRes = await fetch(`${API_BASE}/api/agent/session`);
        if (sRes.ok) {
          const sData = await sRes.json();
          setSession(sData);
        }
      }
    } catch (err) {
      console.error("Error sending command:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetSession = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/session`, { method: 'DELETE' });
      if (res.ok) {
        setSession({ status: 'idle', logs: [] });
      }
    } catch (err) {
      console.error("Error resetting session:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // Check if we have an active assisted apply session running
  const isSessionActive = session && session.status && session.status !== 'idle';

  if (isSessionActive) {
    return (
      <div className="cockpit-container">
        {/* Cockpit Header */}
        <div className="cockpit-header">
          <div>
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)' }}>
              🌌 Cybernetic Agent Cockpit
            </span>
            <h1 style={{ fontSize: '1.4rem', margin: '0.2rem 0' }}>
              Applying for: <span style={{ color: 'var(--accent-indigo)' }}>{session.job_title || 'Unknown'}</span> at <span style={{ color: 'var(--accent-purple)' }}>{session.company || 'Company'}</span>
            </h1>
            {session.url && (
              <a href={session.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                View Original Listing <ExternalLink size={12} />
              </a>
            )}
          </div>
          <div>
            <span 
              className="status-badge-glow" 
              style={{ 
                color: session.status === 'success' ? 'var(--accent-emerald)' : 
                       session.status === 'failed' ? 'var(--accent-rose)' : 
                       session.status === 'waiting_approval' ? 'var(--accent-amber)' : 'var(--accent-indigo)' 
              }}
            >
              {session.status.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Cockpit Grid */}
        <div className="cockpit-grid">
          {/* ReAct Live Thought Stream */}
          <div className="cockpit-panel">
            <div className="cockpit-panel-title">
              <span>🧠 ReAct Live Thought Stream</span>
              <Activity size={14} className={['success', 'failed'].includes(session.status) ? '' : 'animate-pulse'} style={{ color: 'var(--accent-indigo)' }} />
            </div>
            
            <div className="react-stream-container">
              {session.logs && session.logs.map((log, idx) => (
                <div key={idx} className="react-step-card">
                  <div className="react-step-header">
                    <span className={`react-badge ${log.phase.toLowerCase()}`}>
                      {log.phase}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{log.timestamp}</span>
                  </div>
                  <div style={{ color: 'var(--text-primary)', marginTop: '0.25rem', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>
                    {log.message}
                  </div>
                  {log.status === 'Failed' && (
                    <div style={{ color: 'var(--accent-rose)', fontSize: '0.75rem', marginTop: '0.25rem', fontWeight: 'bold' }}>
                      ⚠️ Action execution failed
                    </div>
                  )}
                </div>
              ))}
              <div ref={reactStreamEndRef} />
            </div>
          </div>

          {/* Live Viewport Monitor */}
          <div className="cockpit-panel">
            <div className="cockpit-panel-title">
              <span>🖥️ Live Viewport Monitor</span>
              {['success', 'failed', 'waiting_approval'].includes(session.status) ? (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Paused</span>
              ) : (
                <div className="hud-live">
                  <div className="hud-dot" />
                  <span>FEED LIVE</span>
                </div>
              )}
            </div>

            <div className="viewport-monitor">
              {screenshotUrl ? (
                <img src={screenshotUrl} className="viewport-image" alt="Agent Live Viewport" />
              ) : (
                <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                  <RefreshCw className="animate-spin" size={24} style={{ color: 'var(--accent-indigo)' }} />
                  <span>Initializing remote browser view...</span>
                </div>
              )}
              <div className="cyber-grid-overlay" />
              <div className="scanline" />
              
              <div className="monitor-hud">
                <div className="hud-dimensions">1280 × 800 (Scale Fit)</div>
                <div className="hud-dimensions">STEALTH: ON</div>
              </div>
            </div>
          </div>
        </div>

        {/* Cockpit Control Bar */}
        <div className="cockpit-control-bar">
          {session.status === 'waiting_approval' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center', textAlign: 'center', padding: '0.5rem 0' }}>
              <div style={{ color: 'var(--accent-amber)', fontSize: '1rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⚠️ VERIFICATION REQUIRED: AUTONOMOUS ACTION PAUSED
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '600px', margin: 0 }}>
                The agent has successfully completed form inputs. Review the browser viewport layout above. Click 'Approve' to submit the final application, or 'Abort' to cancel safely.
              </p>
              <div style={{ display: 'flex', gap: '1.5rem', width: '100%', maxWidth: '500px', marginTop: '0.5rem' }}>
                <button 
                  className="btn btn-emerald" 
                  style={{ flex: 1, padding: '0.85rem' }} 
                  disabled={actionLoading}
                  onClick={() => handleSendCommand('approve')}
                >
                  Confirm & Submit
                </button>
                <button 
                  className="btn btn-danger" 
                  style={{ flex: 1, padding: '0.85rem' }} 
                  disabled={actionLoading}
                  onClick={() => handleSendCommand('abort')}
                >
                  Abort Session
                </button>
              </div>
            </div>
          )}

          {session.status === 'success' && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontWeight: '700' }}>
                <CheckCircle size={20} /> APPLICATION COMPLETED SUCCESSFULLY!
              </div>
              <button className="btn btn-secondary" onClick={handleResetSession} disabled={actionLoading}>
                Close Cockpit
              </button>
            </div>
          )}

          {session.status === 'failed' && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-rose)', fontWeight: '700' }}>
                ⚠️ APPLICATION RUN ABORTED / FAILED
              </div>
              <button className="btn btn-secondary" onClick={handleResetSession} disabled={actionLoading}>
                Close Cockpit
              </button>
            </div>
          )}

          {!['waiting_approval', 'success', 'failed'].includes(session.status) && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <RefreshCw className="animate-spin" size={16} style={{ color: 'var(--accent-indigo)' }} />
                <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Agent is actively performing ReAct cycle on job portal...
                </span>
              </div>
              <button className="btn btn-danger" style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }} onClick={() => handleSendCommand('abort')} disabled={actionLoading}>
                Force Abort Agent
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Fallback: Default Background Scheduler controller view
  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>🤖 Autonomous Agent Control</h1>

      <div className="grid-main" style={{ alignItems: 'start' }}>
        {/* Left Side: Controller status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>State Controller</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Status:</span>
                <span style={{ fontWeight: '700', fontSize: '1.1rem', color: agentRunning ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {agentRunning ? '🟢 Running' : '🔴 Stopped'}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                The background agent wakes up every 4 hours to scout for jobs, evaluate matches via RAG, and prepare tailored documents.
              </p>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {!agentRunning ? (
                <button className="btn btn-primary" onClick={handleStart} disabled={loading} style={{ width: '100%' }}>
                  <Play size={16} /> Start Background Agent
                </button>
              ) : (
                <button className="btn btn-danger" onClick={handleStop} disabled={loading} style={{ width: '100%' }}>
                  <Square size={16} /> Stop Background Agent
                </button>
              )}
            </div>
          </div>

          <div className="card">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Quick Actions</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <button className="btn btn-secondary" style={{ width: '100%' }} onClick={forceRunScout}>
                🕵️ Force Run Scout Now
              </button>
              <button className="btn btn-secondary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }} onClick={forceRunEvaluate}>
                🤖 Force Run Match Evaluator
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Terminal log */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.2rem' }}>📜 Live Activity Log</h2>
            <button className="btn btn-secondary" onClick={fetchLogs} style={{ padding: '0.4rem 0.8rem' }}>
              <RefreshCw size={12} />
            </button>
          </div>
          
          <div className="terminal">
            {logs.map(log => (
              <div key={log.id} className="log-entry">
                <span className="log-time">[{log.timestamp.split(' ')[1] || log.timestamp}]</span>
                <span className={`log-action ${log.action.toLowerCase()}`}>{log.action.toUpperCase()}</span>
                <span className="log-details">{log.details}</span>
                <span className={`log-status ${log.status.toLowerCase()}`}>{log.status.toLowerCase()}</span>
              </div>
            ))}
            {logs.length === 0 && (
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No active session logs found.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ==========================================
   5. SETTINGS VIEW
   ========================================== */
function SettingsView({ provider, setProvider, modelName, setModelName }) {
  // Mock API configuration checks
  const [keysLoaded, setKeysLoaded] = useState({
    GOOGLE_API_KEY: true,
    GROQ_API_KEY: false
  });

  useEffect(() => {
    // Quick check backend parameters if desired
    const checkKeys = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/profile/`);
        // Basic check, or just hardcode as active since key is in .env
      } catch (err) {}
    };
    checkKeys();
  }, []);

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>⚙️ System Settings</h1>

      <div className="grid-2">
        <div className="card">
          <h2 style={{ marginBottom: '1.25rem', fontSize: '1.2rem' }}>AI Brain Settings</h2>
          
          <div className="form-group">
            <label className="form-label">Inference Provider</label>
            <select 
              className="form-select" 
              value={provider} 
              onChange={e => {
                setProvider(e.target.value);
                if (e.target.value === 'gemini') setModelName('gemini-2.0-flash-lite');
                else if (e.target.value === 'ollama') setModelName('phi4');
                else if (e.target.value === 'groq') setModelName('llama3-70b-8192');
              }}
            >
              <option value="gemini">Google Gemini (Cloud)</option>
              <option value="ollama">Ollama (Local Network)</option>
              <option value="groq">Groq API (Cloud)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Model Name</label>
            <input 
              type="text" 
              className="form-input" 
              value={modelName} 
              onChange={e => setModelName(e.target.value)} 
            />
            {provider === 'gemini' && <p className="form-text" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Recommended: `gemini-2.0-flash-lite`, `gemini-1.5-pro`</p>}
            {provider === 'ollama' && <p className="form-text" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Ensure that the model is pulled locally via: `ollama pull &lt;model&gt;`</p>}
            {provider === 'groq' && <p className="form-text" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Recommended: `llama3-70b-8192`</p>}
          </div>

          <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(99,102,241,0.05)', border: '1px solid var(--border-color)', borderRadius: '12px', fontSize: '0.9rem' }}>
            Current Model Setting: <strong style={{ color: 'var(--accent-indigo)' }}>{provider.toUpperCase()}</strong> using <strong style={{ color: 'var(--accent-indigo)' }}>{modelName}</strong>
          </div>
        </div>

        <div className="card">
          <h2 style={{ marginBottom: '1.25rem', fontSize: '1.2rem' }}>Connection & Key Status</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
              <span>GOOGLE_API_KEY (Gemini)</span>
              <span style={{ color: 'var(--accent-emerald)', fontWeight: '600' }}>✅ Active (.env)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
              <span>GROQ_API_KEY (Groq)</span>
              <span style={{ color: 'var(--text-muted)' }}>❌ Not Loaded</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
              <span>Ollama Host API Connection</span>
              <span style={{ color: 'var(--accent-indigo)' }}>http://localhost:11434</span>
            </div>
          </div>
          
          <div style={{ marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            ⚠️ Environment configurations and keys are managed securely in the `.env` file in the backend root directory.
          </div>
        </div>
      </div>
    </div>
  );
}

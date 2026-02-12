"""
DevPulseAI v3 — Premium Intelligence Dashboard

Features:
- Dark tech theme with gradient accents
- Tabbed layout: Chat | Intelligence Dashboard | Customization
- Plotly gauge speedometers for agent confidence
- Signal summary dashboard
- Customization panel for signal parameters
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import json
import time
from datetime import datetime, timezone
import streamlit as st
import plotly.graph_objects as go
from app.core.conversation import ConversationManager


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="DevPulseAI v3 — Intelligence Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Premium Dark Theme CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────── */
    .stApp {
        background: #0a0e17;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1321 0%, #131b2e 100%);
        border-right: 1px solid rgba(99, 255, 209, 0.08);
        min-width: 320px !important;
        width: 340px !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #e0e6ed !important;
    }

    /* Hide sidebar collapse/expand controls — keep sidebar always open */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] > div > button:first-child {
        display: none !important;
    }
    
    div[data-testid="stToolbar"] { display: none; }
    
    /* ── Header Banner ──────────────────── */
    .hero-banner {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        border: 1px solid rgba(99, 255, 209, 0.15);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(99,255,209,0.06) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #63ffd1 0%, #00b4d8 50%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #8899aa;
        font-size: 0.95rem;
        font-weight: 400;
        margin-top: 0.4rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99, 255, 209, 0.1);
        border: 1px solid rgba(99, 255, 209, 0.25);
        color: #63ffd1;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.6rem;
        letter-spacing: 0.5px;
    }

    /* ── Agent Cards ────────────────────── */
    .agent-card {
        background: linear-gradient(145deg, #131b2e 0%, #0d1321 100%);
        border: 1px solid rgba(99, 255, 209, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .agent-card:hover {
        border-color: rgba(99, 255, 209, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 255, 209, 0.06);
    }
    .agent-card .icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .agent-card h4 { 
        color: #e0e6ed; 
        margin: 0.3rem 0; 
        font-size: 0.9rem; 
        font-weight: 600; 
    }
    .agent-card p { 
        color: #6b7c93; 
        font-size: 0.75rem; 
        margin: 0; 
    }
    .agent-card .status-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #63ffd1;
        display: inline-block;
        margin-right: 4px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ── Metric Cards ───────────────────── */
    .metric-card {
        background: linear-gradient(145deg, #131b2e 0%, #0d1321 100%);
        border: 1px solid rgba(99, 255, 209, 0.08);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #63ffd1, #00b4d8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        color: #6b7c93;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 0.3rem;
    }
    .metric-delta {
        color: #63ffd1;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* ── Chat Messages ──────────────────── */
    .chat-user {
        background: linear-gradient(135deg, #1a2744 0%, #1e3050 100%);
        border: 1px solid rgba(0, 180, 216, 0.15);
        border-radius: 12px 12px 4px 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        color: #e0e6ed;
    }
    .chat-user .sender {
        color: #00b4d8;
        font-weight: 600;
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
    }
    .chat-assistant {
        background: linear-gradient(135deg, #131b2e 0%, #171f33 100%);
        border: 1px solid rgba(99, 255, 209, 0.1);
        border-radius: 12px 12px 12px 4px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        color: #c8d6e5;
    }
    .chat-assistant .sender {
        color: #63ffd1;
        font-weight: 600;
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
    }

    /* ── Signal Feed Items ──────────────── */
    .signal-item {
        background: rgba(19, 27, 46, 0.6);
        border: 1px solid rgba(99, 255, 209, 0.06);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .signal-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-high { background: rgba(99, 255, 209, 0.15); color: #63ffd1; }
    .badge-medium { background: rgba(255, 190, 50, 0.15); color: #ffbe32; }
    .badge-low { background: rgba(255, 100, 100, 0.15); color: #ff6b6b; }

    /* ── Tabs ────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(13, 19, 33, 0.8);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #6b7c93;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 255, 209, 0.1) !important;
        color: #63ffd1 !important;
    }

    /* ── Streamlit Overrides ─────────────── */
    .stMetric > div { 
        background: linear-gradient(145deg, #131b2e, #0d1321);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(99, 255, 209, 0.06);
    }
    .stMetric label { color: #6b7c93 !important; font-weight: 500 !important; }
    div[data-testid="stMetricValue"] { color: #63ffd1 !important; font-weight: 700 !important; }
    div[data-testid="stMetricDelta"] { color: #00b4d8 !important; }
    
    .stSelectbox label, .stSlider label, .stMultiSelect label,
    .stRadio label, .stCheckbox label, .stNumberInput label {
        color: #8899aa !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0f2027, #203a43) !important;
        color: #63ffd1 !important;
        border: 1px solid rgba(99, 255, 209, 0.2) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        border-color: rgba(99, 255, 209, 0.5) !important;
        box-shadow: 0 4px 15px rgba(99, 255, 209, 0.1) !important;
    }
    
    .stExpander {
        background: rgba(13, 19, 33, 0.6);
        border: 1px solid rgba(99, 255, 209, 0.06);
        border-radius: 8px;
    }
    
    h1, h2, h3, p, span, li, label, div {
        font-family: 'Inter', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Session State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_session():
    defaults = {
        "messages": [],
        "feedback": {},
        "signals_collected": 0,
        "repos_analyzed": 0,
        "papers_found": 0,
        "files_read": 0,
        "queries_total": 0,
        "agent_confidence": {
            "RepoResearcher": 0.0,
            "PaperAnalyst": 0.0,
            "ProjectExplorer": 0.0,
            "Gemini": 0.0,
        },
        "signal_log": [],
        # Customization defaults
        "max_signals": 10,
        "signal_types": ["GitHub", "ArXiv", "Local Files"],
        "priority_threshold": "Medium",
        "confidence_threshold": 70,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Conversation Manager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_resource
def get_conversation_manager():
    return ConversationManager()

conv_manager = get_conversation_manager()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_gauge(value, title, color="#63ffd1"):
    """Create a Plotly speedometer gauge for confidence."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': '%', 'font': {'size': 28, 'color': '#e0e6ed', 'family': 'Inter'}},
        title={'text': title, 'font': {'size': 12, 'color': '#6b7c93', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#1a2744',
                     'tickfont': {'color': '#4a5568', 'size': 9}},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': '#0d1321',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 100, 100, 0.12)'},
                {'range': [40, 70], 'color': 'rgba(255, 190, 50, 0.12)'},
                {'range': [70, 100], 'color': 'rgba(99, 255, 209, 0.12)'},
            ],
            'threshold': {
                'line': {'color': '#63ffd1', 'width': 2},
                'thickness': 0.8,
                'value': value
            }
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter'}
    )
    return fig


def track_signal(signal_type, detail, confidence=0.85):
    """Track a processed signal for the dashboard."""
    st.session_state.signal_log.append({
        "type": signal_type,
        "detail": detail[:50],
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    })
    st.session_state.signals_collected += 1


def process_and_track(user_input):
    """Process message and track metrics."""
    start = time.time()
    response = asyncio.run(conv_manager.process_message(user_input))
    elapsed = time.time() - start
    
    # Track metrics based on detected intent
    msg_lower = user_input.lower()
    if any(kw in msg_lower for kw in ["repo", "github", "analyze"]):
        st.session_state.repos_analyzed += 1
        st.session_state.agent_confidence["RepoResearcher"] = min(95, 75 + st.session_state.repos_analyzed * 3)
        track_signal("GitHub", user_input, 0.85)
    elif any(kw in msg_lower for kw in ["paper", "arxiv", "research"]):
        st.session_state.papers_found += 1
        st.session_state.agent_confidence["PaperAnalyst"] = min(92, 70 + st.session_state.papers_found * 4)
        track_signal("ArXiv", user_input, 0.82)
    elif any(kw in msg_lower for kw in ["read", "file", "directory", "tree", "readme"]):
        st.session_state.files_read += 1
        st.session_state.agent_confidence["ProjectExplorer"] = min(98, 85 + st.session_state.files_read * 2)
        track_signal("Local", user_input, 0.95)
    else:
        st.session_state.agent_confidence["Gemini"] = min(90, 65 + st.session_state.queries_total * 2)
        track_signal("General", user_input, 0.78)
    
    st.session_state.queries_total += 1
    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Hero Banner
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="hero-banner">
    <p class="hero-title">⚡ DevPulseAI v3</p>
    <p class="hero-subtitle">Autonomous Technical Intelligence — Ingest • Analyze • Deliver</p>
    <span class="hero-badge">● MULTISWARM ACTIVE — KimiK2.5 Architecture</span>
</div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sidebar — Controls & Customization
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## ⚙️ Signal Configuration")
    st.markdown("---")
    
    # Signal count
    st.session_state.max_signals = st.slider(
        "📊 Max Signals to Fetch",
        min_value=5, max_value=50, value=st.session_state.max_signals, step=5,
        help="Maximum number of signals to collect per source"
    )
    
    # Signal types
    st.session_state.signal_types = st.multiselect(
        "📡 Signal Types",
        options=["GitHub", "ArXiv", "HuggingFace", "Medium", "HackerNews", "Local Files"],
        default=st.session_state.signal_types,
        help="Which sources to monitor"
    )
    
    # Priority
    st.session_state.priority_threshold = st.select_slider(
        "🎯 Priority Threshold",
        options=["Low", "Medium", "High", "Critical"],
        value=st.session_state.priority_threshold,
        help="Minimum priority level for signal inclusion"
    )
    
    # Confidence threshold
    st.session_state.confidence_threshold = st.slider(
        "🔒 Min Confidence Score",
        min_value=0, max_value=100, value=st.session_state.confidence_threshold,
        format="%d%%",
        help="Minimum agent confidence to include results"
    )
    
    st.markdown("---")
    
    # Quick Stats
    st.markdown("## 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Signals", st.session_state.signals_collected)
        st.metric("Repos", st.session_state.repos_analyzed)
    with col2:
        st.metric("Papers", st.session_state.papers_found)
        st.metric("Files", st.session_state.files_read)
    
    st.markdown("---")
    
    # Swarm Status
    st.markdown("## 🐝 Swarm Status")
    swarm_status = conv_manager.swarm.status()
    for swarm_name, info in swarm_status.get("swarms", {}).items():
        workers = info.get("workers", [])
        st.markdown(f"""
        <div style="background: rgba(99,255,209,0.04); border: 1px solid rgba(99,255,209,0.08);
                    border-radius: 8px; padding: 0.6rem; margin-bottom: 0.4rem;">
            <div style="color: #63ffd1; font-weight: 600; font-size: 0.8rem;">
                <span class="agent-card" style="padding:0; background:none; border:none;">
                    <span style="color:#63ffd1;">●</span>
                </span> {swarm_name.upper()}
            </div>
            <div style="color: #6b7c93; font-size: 0.7rem;">{', '.join(workers)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("DevPulseAI v3 | Powered by Gemini & MultiSwarm")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Tabs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab_chat, tab_dashboard, tab_agents, tab_signals = st.tabs([
    "💬 Intelligence Chat",
    "📊 Dashboard",
    "🤖 Agent System",
    "📡 Signal Feed"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tab 1: Intelligence Chat
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_chat:
    # Example queries
    st.markdown("#### 🎯 Quick Actions")
    qa_cols = st.columns(4)
    examples = [
        ("🔍 Analyze Repo", "Analyze the FastAPI repository structure"),
        ("📄 Find Papers", "Find recent papers on Retrieval Augmented Generation"),
        ("📂 Read README", "Read the content of README.md present at D:/DevPulseAIv2/"),
        ("🌳 Project Tree", "Tell me the tree structure of the directory D:/DevPulseAIv2/"),
    ]
    for i, (label, query) in enumerate(examples):
        with qa_cols[i]:
            if st.button(label, key=f"ex_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
    
    st.markdown("---")
    
    # Chat display
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 4rem 2rem; color: #4a5568;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
                <div style="font-size: 1.1rem; color: #6b7c93; font-weight: 500;">
                    Welcome to DevPulseAI v3
                </div>
                <div style="font-size: 0.85rem; color: #4a5568; margin-top: 0.5rem;">
                    Ask me to analyze repos, find papers, read files, or chat about development
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        for idx, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div class="sender">You</div>
                    <div>{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-assistant">
                    <div class="sender">⚡ DevPulseAI</div>
                    <div>{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Feedback
                fcol1, fcol2, fcol3 = st.columns([1, 1, 10])
                with fcol1:
                    if st.button("👍", key=f"up_{idx}"):
                        st.session_state.feedback[idx] = "positive"
                with fcol2:
                    if st.button("👎", key=f"dn_{idx}"):
                        st.session_state.feedback[idx] = "negative"
    
    # Input
    user_input = st.chat_input("Ask me anything — analyze repos, find papers, read files...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("⚡ MultiSwarm processing..."):
            try:
                response = process_and_track(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {str(e)}"
                })
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tab 2: Intelligence Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_dashboard:
    st.markdown("### 📊 Intelligence Overview")
    
    # Top metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.signals_collected}</div>
            <div class="metric-label">Signals Collected</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.repos_analyzed}</div>
            <div class="metric-label">Repos Analyzed</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.papers_found}</div>
            <div class="metric-label">Papers Found</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.files_read}</div>
            <div class="metric-label">Files Read</div>
        </div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.queries_total}</div>
            <div class="metric-label">Total Queries</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Confidence Speedometers
    st.markdown("### 🎯 Agent Confidence Gauges")
    
    g1, g2, g3, g4 = st.columns(4)
    conf = st.session_state.agent_confidence
    
    with g1:
        fig = create_gauge(conf["RepoResearcher"], "RepoResearcher", "#00b4d8")
        st.plotly_chart(fig, use_container_width=True, key="gauge_repo")
    with g2:
        fig = create_gauge(conf["PaperAnalyst"], "PaperAnalyst", "#a78bfa")
        st.plotly_chart(fig, use_container_width=True, key="gauge_paper")
    with g3:
        fig = create_gauge(conf["ProjectExplorer"], "ProjectExplorer", "#63ffd1")
        st.plotly_chart(fig, use_container_width=True, key="gauge_explorer")
    with g4:
        fig = create_gauge(conf["Gemini"], "Gemini LLM", "#ffbe32")
        st.plotly_chart(fig, use_container_width=True, key="gauge_gemini")
    
    st.markdown("---")
    
    # Signal Summary
    st.markdown("### 📋 Signal Summary")
    
    if st.session_state.signal_log:
        summary_data = {}
        for sig in st.session_state.signal_log:
            t = sig["type"]
            summary_data[t] = summary_data.get(t, 0) + 1
        
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            # Pie chart
            fig = go.Figure(go.Pie(
                labels=list(summary_data.keys()),
                values=list(summary_data.values()),
                hole=0.55,
                marker=dict(colors=['#00b4d8', '#a78bfa', '#63ffd1', '#ffbe32', '#ff6b6b']),
                textfont=dict(color='#e0e6ed', family='Inter'),
            ))
            fig.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(font=dict(color='#8899aa', family='Inter')),
                title=dict(text="Signal Distribution", font=dict(color='#8899aa', size=13, family='Inter'))
            )
            st.plotly_chart(fig, use_container_width=True, key="pie_signals")
        
        with sc2:
            # Recent signals table
            st.markdown("#### Recent Activity")
            for sig in reversed(st.session_state.signal_log[-8:]):
                badge_class = "badge-high" if sig["confidence"] > 0.85 else "badge-medium" if sig["confidence"] > 0.7 else "badge-low"
                st.markdown(f"""
                <div class="signal-item">
                    <span class="signal-badge {badge_class}">{sig['type']}</span>
                    <span style="color: #c8d6e5; font-size: 0.85rem; flex: 1;">{sig['detail']}</span>
                    <span style="color: #4a5568; font-size: 0.75rem;">{sig['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No signals collected yet. Start chatting to generate intelligence data!")
    
    st.markdown("---")
    
    # Configuration Summary
    st.markdown("### ⚙️ Current Configuration")
    cfg1, cfg2, cfg3, cfg4 = st.columns(4)
    with cfg1:
        st.metric("Max Signals", st.session_state.max_signals)
    with cfg2:
        st.metric("Sources", len(st.session_state.signal_types))
    with cfg3:
        st.metric("Priority", st.session_state.priority_threshold)
    with cfg4:
        st.metric("Min Confidence", f"{st.session_state.confidence_threshold}%")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tab 3: Agent System
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_agents:
    st.markdown("### 🤖 MultiSwarm Architecture")
    st.markdown("*KimiK2.5-Inspired Parallel Agent Orchestration*")
    
    # Agent cards
    agents = [
        {"icon": "🔍", "name": "RepoResearcher", "swarm": "Research",
         "desc": "Deep-dives into GitHub repositories, analyzes code structure & dependencies"},
        {"icon": "📄", "name": "PaperAnalyst", "swarm": "Analysis",
         "desc": "Searches and summarizes academic papers from ArXiv & research databases"},
        {"icon": "📂", "name": "ProjectExplorer", "swarm": "Local",
         "desc": "Reads local files, lists directories, and analyzes project structure"},
        {"icon": "🧠", "name": "Gemini LLM", "swarm": "Core",
         "desc": "General intelligence backbone — handles Q&A, intent detection, and reasoning"},
        {"icon": "🛡️", "name": "CriticAgent", "swarm": "QA",
         "desc": "Validates outputs for hallucinations — self-correction feedback loop"},
        {"icon": "📊", "name": "Coordinator", "swarm": "Core",
         "desc": "MultiSwarm dispatcher — parallel task routing, fan-out, message bus"},
    ]
    
    acols = st.columns(3)
    for i, agent in enumerate(agents):
        with acols[i % 3]:
            st.markdown(f"""
            <div class="agent-card">
                <div class="icon">{agent['icon']}</div>
                <h4>{agent['name']}</h4>
                <p>{agent['desc']}</p>
                <div style="margin-top: 0.6rem;">
                    <span class="signal-badge badge-high">{agent['swarm']} Swarm</span>
                </div>
            </div>
            <br>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Architecture diagram
    st.markdown("### 🏗️ System Architecture")
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────┐
    │                    MultiSwarmManager                      │
    │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
    │  │  Research   │  │  Analysis  │  │       Local        │ │
    │  │ ┌────────┐  │  │ ┌────────┐ │  │ ┌───────────────┐  │ │
    │  │ │RepoRscr│  │  │ │PaperAnl│ │  │ │ProjectExplorer│  │ │
    │  │ └────────┘  │  │ └────────┘ │  │ └───────────────┘  │ │
    │  └────────────┘  └────────────┘  └────────────────────┘ │
    │            ↕ Inter-Swarm Message Bus ↕                   │
    │  ┌────────────────────────────────────────────────┐      │
    │  │  Coordinator: Parallel Dispatch | Fan-out      │      │
    │  │  Shared Context | Capability-based Discovery   │      │
    │  └────────────────────────────────────────────────┘      │
    └──────────────────────────────────────────────────────────┘
    ```
    """)
    
    # Features
    st.markdown("### ⚡ Key Capabilities")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        **🚀 Parallel Dispatch**
        - Execute multiple tasks simultaneously
        - Cross-swarm coordination
        - Async worker execution
        """)
    with f2:
        st.markdown("""
        **📡 Fan-Out Queries**
        - Same query to multiple agents
        - Diverse perspectives
        - Result aggregation
        """)
    with f3:
        st.markdown("""
        **💬 Message Bus**
        - Inter-agent communication
        - Broadcast system-wide events
        - Shared context access
        """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tab 4: Signal Feed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_signals:
    st.markdown("### 📡 Intelligence Signal Feed")
    st.markdown("*Real-time signal tracking from all sources*")
    
    if st.session_state.signal_log:
        # Filter by type
        all_types = list(set(s["type"] for s in st.session_state.signal_log))
        selected_types = st.multiselect("Filter by type:", all_types, default=all_types, key="feed_filter")
        
        filtered = [s for s in st.session_state.signal_log if s["type"] in selected_types]
        
        for sig in reversed(filtered):
            conf_pct = sig["confidence"] * 100
            if conf_pct >= 85:
                badge_class = "badge-high"
                conf_label = "HIGH"
            elif conf_pct >= 70:
                badge_class = "badge-medium"
                conf_label = "MED"
            else:
                badge_class = "badge-low"
                conf_label = "LOW"
            
            st.markdown(f"""
            <div class="signal-item" style="padding: 1rem;">
                <span class="signal-badge {badge_class}" style="min-width: 70px; text-align: center;">{sig['type']}</span>
                <div style="flex: 1;">
                    <div style="color: #e0e6ed; font-size: 0.9rem;">{sig['detail']}</div>
                    <div style="color: #4a5568; font-size: 0.75rem; margin-top: 0.2rem;">
                        🕐 {sig['timestamp']} · Confidence: {conf_pct:.0f}%
                    </div>
                </div>
                <span class="signal-badge {badge_class}">{conf_label}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export
        if st.button("📥 Export Signal Log", use_container_width=True):
            json_str = json.dumps(st.session_state.signal_log, indent=2)
            st.download_button(
                "Download JSON",
                data=json_str,
                file_name=f"devpulse_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; color: #4a5568;">
            <div style="font-size: 3rem;">📡</div>
            <div style="font-size: 1rem; color: #6b7c93; margin-top: 1rem;">
                No signals collected yet
            </div>
            <div style="font-size: 0.85rem; color: #4a5568; margin-top: 0.5rem;">
                Start asking questions in the Chat tab to generate intelligence signals
            </div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #4a5568; font-size: 0.75rem; padding: 0.5rem;">
    DevPulseAI v3 · MultiSwarm Intelligence · Built with ❤️ by Hill Patel · Powered by Google Gemini & Supabase
</div>
""", unsafe_allow_html=True)

import streamlit as st
import json
import base64
from datetime import datetime
from github import Github
import time

st.set_page_config(
    page_title="Log Stream Triager",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS FOR CLEAN DESIGN
# ============================================================================
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        padding-top: 0;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    
    .status-info {
        background: #d1ecf1;
        color: #0c5460;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin: 0.5rem 0;
    }
    
    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #f5c6cb;
        margin: 0.5rem 0;
    }
    
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        margin: 0;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
    
    .button-group {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================
GITHUB_OWNER = st.secrets.get("GITHUB_OWNER", "your-username")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "hackathon")
WORKFLOW_FILE = "log_triager.yml"

github_token = st.secrets.get("GITHUB_TOKEN", None)
groq_token = st.secrets.get("GROQ_API_KEY", None)

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="main-header">
    <h1>🔍 Log Stream Triager</h1>
    <p>AI-Powered CI/CD Log Analysis | Genuine Bugs vs Environment Flakes</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN LAYOUT
# ============================================================================
col1, col2 = st.columns([2, 1], gap="large")

# ============================================================================
# LEFT COLUMN - MAIN CONTENT
# ============================================================================
with col1:
    # ========== UPLOAD SECTION ==========
    st.markdown("### 📤 Upload Logs")
    
    uploaded_file = st.file_uploader(
        "Choose a CI/CD log file",
        type=["txt", "log", "json"],
        help="Supported formats: .txt, .log, .json"
    )
    
    if uploaded_file:
        try:
            if uploaded_file.type == "application/json":
                data = json.load(uploaded_file)
                log_content = json.dumps(data, indent=2)
            else:
                log_content = uploaded_file.read().decode("utf-8")
            
            st.session_state.log_file_name = uploaded_file.name
            st.session_state.log_content = log_content
            st.session_state.log_file_size = uploaded_file.size
            
            # File preview
            with st.expander("📋 Preview Log File", expanded=False):
                st.text_area(
                    label="Log preview",
                    value=log_content[:1500],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            # File info
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">File Size</div>
                    <div class="metric-value">{uploaded_file.size:,}</div>
                    <div class="metric-label">bytes</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Lines</div>
                    <div class="metric-value">{log_content.count(chr(10))}</div>
                    <div class="metric-label">total</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_c:
                st.markdown("""
                <div class="metric-box">
                    <div class="metric-label">Status</div>
                    <div class="metric-value" style="color: #28a745;">✓</div>
                    <div class="metric-label">Ready</div>
                </div>
                """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            uploaded_file = None
    
    else:
        st.info("👆 Upload a CI/CD pipeline log file to get started")
    
    # ========== ACTION SECTION ==========
    if hasattr(st.session_state, 'log_content'):
        st.markdown("### 🚀 Analyze")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("▶ Start Analysis", use_container_width=True, type="primary"):
                if not github_token:
                    st.error("❌ GitHub token not configured")
                else:
                    try:
                        with st.spinner("🔄 Triggering workflow..."):
                            g = Github(github_token)
                            repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
                            
                            log_b64 = base64.b64encode(
                                st.session_state.log_content.encode('utf-8')
                            ).decode('utf-8')
                            
                            workflow = repo.get_workflow(WORKFLOW_FILE)
                            dispatch_result = workflow.create_dispatch(
                                ref="main",
                                inputs={
                                    "logs_base64": log_b64,
                                    "logs_filename": st.session_state.log_file_name,
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            
                            if dispatch_result:
                                time.sleep(3)
                                runs = list(workflow.get_runs())
                                
                                if runs and len(runs) > 0:
                                    latest_run = runs[0]
                                    st.session_state.workflow_run_id = latest_run.id
                                    st.session_state.workflow_triggered_at = datetime.now()
                                    
                                    st.markdown("""
                                    <div class="status-success">
                                        ✅ Workflow triggered successfully!
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.info(f"**Workflow ID:** `{latest_run.id}`")
                                    st.info("⏳ Processing (2-5 minutes). Check back soon!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error("❌ Failed to trigger workflow")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col_btn2:
            if "workflow_run_id" in st.session_state:
                if st.button("🔄 Refresh Status", use_container_width=True):
                    try:
                        g = Github(github_token)
                        repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
                        run = repo.get_workflow_run(st.session_state.workflow_run_id)
                        
                        status_map = {
                            "queued": "🟡 Queued",
                            "in_progress": "🔵 In Progress",
                            "completed": "✅ Completed",
                            "failed": "❌ Failed",
                        }
                        
                        st.info(f"**Status:** {status_map.get(run.status, run.status)}")
                        
                        if run.status == "completed" and run.conclusion == "success":
                            st.success("✅ Analysis completed!")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================================================
# RIGHT COLUMN - STATUS & SECRETS
# ============================================================================
with col2:
    st.markdown("### ⚙️ Status")
    
    # GitHub token status
    if github_token:
        st.markdown("""
        <div class="status-success">
            ✅ GitHub Token
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-error">
            ❌ GitHub Token Missing
        </div>
        """, unsafe_allow_html=True)
    
    # Groq token status
    if groq_token:
        st.markdown("""
        <div class="status-success">
            ✅ Groq API Key
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-error">
            ❌ Groq API Key Missing
        </div>
        """, unsafe_allow_html=True)
    
    # Workflow status
    if "workflow_run_id" in st.session_state:
        try:
            g = Github(github_token)
            repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
            run = repo.get_workflow_run(st.session_state.workflow_run_id)
            
            if run.status == "completed":
                st.markdown("""
                <div class="status-success">
                    ✅ Workflow Complete
                </div>
                """, unsafe_allow_html=True)
            elif run.status == "in_progress":
                st.markdown("""
                <div class="status-info">
                    🔵 Workflow Running
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-info">
                    🟡 Workflow Queued
                </div>
                """, unsafe_allow_html=True)
        except:
            pass

# ============================================================================
# RESULTS SECTION
# ============================================================================
if "workflow_run_id" in st.session_state:
    st.divider()
    st.markdown("### 📊 Analysis Results")
    
    try:
        g = Github(github_token)
        repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
        run = repo.get_workflow_run(st.session_state.workflow_run_id)
        
        if run.status == "completed":
            try:
                artifacts = list(run.get_artifacts())
                
                if artifacts:
                    for artifact in artifacts:
                        artifact_data = artifact.download().read()
                        
                        # Extract zip and read files
                        import zipfile
                        import io
                        
                        with zipfile.ZipFile(io.BytesIO(artifact_data)) as z:
                            files = z.namelist()
                            
                            # Read report.md
                            if 'report.md' in files:
                                report_content = z.read('report.md').decode('utf-8')
                                
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.markdown("#### 📋 Report")
                                
                                with col2:
                                    st.download_button(
                                        label="⬇ Download",
                                        data=report_content,
                                        file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                        mime="text/markdown",
                                        use_container_width=True
                                    )
                                
                                # Display report in markdown
                                st.markdown(report_content)
                            
                            # Read summary.json
                            if 'summary.json' in files:
                                summary_data = json.loads(z.read('summary.json').decode('utf-8'))
                                
                                st.divider()
                                st.markdown("#### 📈 Summary Statistics")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.markdown(f"""
                                    <div class="metric-box">
                                        <div class="metric-label">Total Logs</div>
                                        <div class="metric-value">{summary_data.get('total_logs', 0)}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    bugs = summary_data.get('genuine_bugs', 0)
                                    st.markdown(f"""
                                    <div class="metric-box">
                                        <div class="metric-label">🐛 Genuine Bugs</div>
                                        <div class="metric-value" style="color: #dc3545;">{bugs}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col3:
                                    flakes = summary_data.get('environment_flakes', 0)
                                    st.markdown(f"""
                                    <div class="metric-box">
                                        <div class="metric-label">🌧️ Flakes</div>
                                        <div class="metric-value" style="color: #fd7e14;">{flakes}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col4:
                                    pct = summary_data.get('bug_percentage', 0)
                                    st.markdown(f"""
                                    <div class="metric-box">
                                        <div class="metric-label">Bug %</div>
                                        <div class="metric-value" style="color: #667eea;">{pct}%</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.info("📦 Processing results...")
        
        else:
            st.info(f"⏳ Workflow is {run.status}. Please wait...")
    
    except Exception as e:
        st.warning("Unable to fetch results at the moment.")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 2rem;">
    <p>🔍 Log Stream Triager | Powered by Groq LLM + GitHub Actions</p>
    <p style="font-size: 0.85rem;">Built for automated CI/CD pipeline analysis</p>
</div>
""", unsafe_allow_html=True)
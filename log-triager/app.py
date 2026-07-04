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
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONFIGURATION - Read from Secrets Automatically
# ============================================================================
GITHUB_OWNER = st.secrets.get("GITHUB_OWNER", "your-github-username")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "hackathon")
WORKFLOW_FILE = "log_triager.yml"

# Get tokens from secrets (no UI input needed!)
github_token = st.secrets.get("GITHUB_TOKEN", None)
groq_token = st.secrets.get("GROQ_API_KEY", None)

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.title("⚙️ Configuration")

# Display status of secrets
if github_token:
    st.sidebar.success("✅ GitHub Token: Configured from Secrets")
else:
    st.sidebar.error("❌ GitHub Token: Not found in Secrets")

if groq_token:
    st.sidebar.success("✅ Groq API Key: Configured from Secrets")
else:
    st.sidebar.error("❌ Groq API Key: Not found in Secrets")

# Optional: Allow manual override (for testing)
with st.sidebar.expander("🔧 Override Secrets (Optional)"):
    manual_github = st.text_input(
        "Manual GitHub Token",
        type="password",
        help="Leave empty to use secrets"
    )
    manual_groq = st.text_input(
        "Manual Groq API Key",
        type="password",
        help="Leave empty to use secrets"
    )
    
    # Use manual if provided, otherwise use secrets
    if manual_github:
        github_token = manual_github
    if manual_groq:
        groq_token = manual_groq

st.sidebar.divider()
st.sidebar.markdown(
    """
    **How it works:**
    1. Upload CI/CD pipeline log files
    2. Review the log preview
    3. Click 'Trigger Workflow'
    4. GitHub Actions processes logs using Groq LLM
    5. Get markdown report with bug/flake classification
    """
)

# ============================================================================
# MAIN INTERFACE
# ============================================================================
st.title("🔍 Log Stream Build Triager & Filter")
st.markdown(
    """
    **Automated CI/CD pipeline log analysis using Groq LLM.**
    
    Upload your CI/CD failure logs and get AI-powered classification:
    - 🐛 **Genuine Bugs** (require code fixes)
    - 🌧️ **Environment Flakes** (transient issues, auto-recover)
    """
)

# ============================================================================
# MAIN CONTENT
# ============================================================================

tab1, tab2 = st.tabs(["📤 Upload & Analyze", "📊 View Results"])

with tab1:
    st.subheader("Upload CI/CD Pipeline Logs")
    
    st.info(
        "📝 **Supported formats:** .txt, .log, .json\n\n"
        "**Example log structure:**\n"
        "```\n"
        "[2024-01-15T10:23:47Z] ERROR: NullPointerException\n"
        "java.lang.NullPointerException: Cannot invoke...\n"
        "```"
    )
    
    uploaded_file = st.file_uploader(
        "Choose a log file to analyze",
        type=["txt", "log", "json"],
        help="Raw CI/CD pipeline failure logs"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
        
        if uploaded_file.type == "application/json":
            try:
                data = json.load(uploaded_file)
                log_content = json.dumps(data, indent=2)
                st.json(data)
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file")
                uploaded_file = None
                log_content = None
        else:
            try:
                log_content = uploaded_file.read().decode("utf-8")
                st.text_area(
                    "Log File Preview",
                    log_content[:2000],
                    height=300,
                    disabled=True
                )
            except UnicodeDecodeError:
                st.error("❌ Unable to read file. Please upload a text-based log file.")
                uploaded_file = None
                log_content = None
        
        if uploaded_file and log_content:
            st.session_state.log_file_name = uploaded_file.name
            st.session_state.log_content = log_content
            st.session_state.log_file_size = uploaded_file.size
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{uploaded_file.size:,} bytes")
            with col2:
                line_count = log_content.count('\n')
                st.metric("Lines", f"{line_count:,}")
            with col3:
                st.metric("Status", "Ready ✅")
    else:
        st.info("👈 Upload a log file to begin analysis")

# ============================================================================
# TRIGGER SECTION
# ============================================================================

st.divider()
st.subheader("🚀 Analysis Controls")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🚀 TRIGGER ANALYSIS", use_container_width=True, type="primary"):
        if not github_token:
            st.error("❌ GitHub token not configured. Add to Streamlit Cloud Secrets.")
        elif not hasattr(st.session_state, 'log_content'):
            st.error("❌ Please upload a log file first.")
        else:
            try:
                with st.spinner("🔄 Triggering GitHub Actions workflow..."):
                    g = Github(github_token)
                    repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
                    
                    log_b64 = base64.b64encode(
                        st.session_state.log_content.encode('utf-8')
                    ).decode('utf-8')
                    
                    workflow = repo.get_workflow(WORKFLOW_FILE)
                    run = workflow.create_dispatch(
                        ref="main",
                        inputs={
                            "logs_base64": log_b64,
                            "logs_filename": st.session_state.log_file_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    st.session_state.workflow_run_id = run.id
                    st.session_state.workflow_triggered_at = datetime.now()
                    
                    st.success(f"✅ Workflow triggered successfully!")
                    st.info(
                        f"**Workflow ID:** {run.id}\n\n"
                        "**Processing time:** 2-5 minutes\n\n"
                        "Check back in a few minutes to view results."
                    )
                    time.sleep(2)
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error triggering workflow:\n\n{str(e)}")

with col2:
    if st.button("🔄 CHECK STATUS", use_container_width=True):
        if "workflow_run_id" not in st.session_state:
            st.warning("⚠️ No active workflow. Trigger an analysis first.")
        else:
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
                
                status_display = status_map.get(run.status, run.status)
                st.info(f"**Status:** {status_display}")
                
                if run.status == "completed":
                    if run.conclusion == "success":
                        st.success(f"✅ Workflow completed successfully!")
                    else:
                        st.error(f"❌ Workflow failed: {run.conclusion}")
                
            except Exception as e:
                st.error(f"❌ Error checking status: {str(e)}")

with col3:
    st.markdown(
        """
        **Workflow Steps:**
        1. Parse & clean logs (SDET 1)
        2. AI classification with Groq (SDET 2)
        3. Validation & cross-check (SDET 3)
        4. Route to categories (SDET 4)
        5. Generate markdown report (SDET 5)
        """
    )

# ============================================================================
# RESULTS TAB
# ============================================================================

with tab2:
    st.subheader("📊 Analysis Results")
    
    if "workflow_run_id" not in st.session_state:
        st.info(
            "👈 Results will appear here after you trigger an analysis.\n\n"
            "**What you'll see:**\n"
            "- Classification summary (bugs vs flakes)\n"
            "- Detailed findings for each log\n"
            "- Actionable recommendations\n"
            "- Download link to full report"
        )
    else:
        try:
            g = Github(github_token)
            repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
            run = repo.get_workflow_run(st.session_state.workflow_run_id)
            
            if run.status != "completed":
                st.warning(f"🔄 Workflow is {run.status}. Check back soon!")
            else:
                st.success("✅ Analysis completed!")
                
                try:
                    artifacts = list(run.get_artifacts())
                    if artifacts:
                        st.info(f"Found {len(artifacts)} artifact(s)")
                        for artifact in artifacts:
                            st.write(f"📦 **{artifact.name}**")
                            st.download_button(
                                label=f"Download {artifact.name}",
                                data=artifact.download().read(),
                                file_name=f"{artifact.name}.zip",
                                mime="application/zip"
                            )
                except Exception as e:
                    st.info("Check your GitHub repo for the generated report.md file")
                
        except Exception as e:
            st.warning("⚠️ Unable to fetch results. Check your GitHub Actions manually.")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(
    "Log Stream Triager | Powered by Groq LLM + GitHub Actions\n"
    "[Groq Docs](https://console.groq.com/docs) | "
    "[GitHub Actions](https://docs.github.com/en/actions) | "
    "[Source](https://github.com)"
)
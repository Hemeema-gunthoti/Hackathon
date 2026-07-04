# 🔍 Log Stream Build Triager & Filter (Groq Edition)

Automated CI/CD pipeline log analysis using **Groq LLM**.

## Features

- **Upload CI/CD Logs** via Streamlit web interface
- **Groq LLM Classification** (fast, low-cost)
- **5-Step Analysis Pipeline**:
  1. Log parsing & cleaning
  2. AI-powered classification (genuine bugs vs environment flakes)
  3. Validation & cross-check
  4. Categorization
  5. Markdown report generation
- **GitHub Actions Integration** for automated processing
- **No Synthetic Generation** - pure log file upload

## Quick Start

### 1. Get API Keys

**Groq API Key:**
- Go to: https://console.groq.com/keys
- Create key: `log-triager`
- Copy: `gsk_...`

**GitHub PAT:**
- Go to: https://github.com/settings/tokens
- Create token (classic): `log-triager-workflow`
- Select scopes: `repo`, `workflow`
- Copy: `ghp_...`

### 2. Setup GitHub Secrets

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `GROQ_API_KEY` = `gsk_...`
   - `GITHUB_TOKEN` = `ghp_...`

### 3. Create Files in GitHub

Use GitHub web UI to create all files from repo root

### 4. Deploy Streamlit App

1. Go to: https://streamlit.io/cloud
2. Connect GitHub repo
3. Add secrets:
   - `GROQ_API_KEY`
   - `GITHUB_TOKEN`
   - `GITHUB_OWNER` = your GitHub username
   - `GITHUB_REPO` = `log-triager`
4. Deploy!

### 5. Upload Logs & Analyze

1. Open your Streamlit app
2. Upload `.txt`, `.log`, or `.json` file
3. Click **"🚀 TRIGGER ANALYSIS"**
4. Check GitHub Actions for progress
5. Download markdown report from artifacts

## File Format

Supported log formats:
- **Plain text** (.txt, .log)
- **JSON** (.json)

## Classification Categories

### 🐛 Genuine Bugs
- NullPointerException, IndexOutOfBounds
- Logic errors, type casting issues
- Constraint violations

### 🌧️ Environment Flakes
- Network timeouts
- Connection pool issues
- DNS failures
- Cloud provider throttling

## Cost

- **Groq API**: Free tier available
- **GitHub Actions**: Free tier
- **Streamlit Cloud**: Free tier

---

**Log Stream Triager** | Powered by Groq + GitHub Actions
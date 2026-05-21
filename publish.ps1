# Streamlit 로컬 실행 (LAN 접속: http://<PC-IP>:8501)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

$py = ".\.venv\Scripts\python.exe"
& $py -m streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0

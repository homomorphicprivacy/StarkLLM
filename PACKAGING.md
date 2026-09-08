# StarkLLM Packaging Guide

This document describes how to create a clean, distributable zip package of StarkLLM for the Windows Research Beta release. 

## Automated Packaging (Recommended)

To streamline the release process and guarantee that no personal data is leaked, use the provided PowerShell helper script:

1. Right-click **`package-release.ps1`** and select **Run with PowerShell**.
2. Enter the version number when prompted (e.g., `1.0.0`).
3. The script will automatically create a zip file named `StarkLLM-Windows-Research-Beta-v1.0.0.zip` in the project root.

The script safely copies only the required source files and ignores sensitive local data, caches, and node_modules.

---

## Manual Packaging (Reference)

If you prefer to zip the package manually, adhere strictly to the following Inclusion and Exclusion lists to avoid leaking private data.

### 1. Inclusion List
The release zip **must include** these files and directories:
- `backend/` (source code)
- `frontend/` (source code)
- `docker-compose.yml`
- `start.bat`
- `start.cmd`
- `unblock.bat`
- `README.md`
- `RELEASE_CHECKLIST.md`
- `PACKAGING.md`
- `.env.example`

### 2. Exclusion List
The release zip **must NOT include**:
- `data/` directory (contains SQLite database, Vector DB chunks, and uploaded documents)
- `knowledge_base_data/` directory (user's personal mapped KB files)
- `.env` file (contains your local environment configuration or secrets)
- `node_modules/` or `dist/` inside frontend
- `venv/`, `.venv/`, `.pytest_cache/`, or `__pycache__/` inside backend
- `.git/` or `.gitignore`
- Any temporary IDE files (`.vscode`, `.gemini`, `scratch`, screenshots, test scripts)

---

## Sanity Notes for Distribution

When distributing the package or writing release notes on GitHub/starkllm.com, always add these explicit notes:

- **Requirements**: Users must install **Docker Desktop** and **Ollama** independently before running `start.bat`.
- **Status**: This is a **Research Beta**.
- **License/Cost**: StarkLLM is **completely free** and **open source**.
- **Liability**: The software is provided "as is", with no warranty and no liability for data loss.

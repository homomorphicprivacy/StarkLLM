# StarkLLM Release Notes

**Latest branch:** `phase-1.5-citations-and-gkb-sync`  
**Base version:** StarkLLM v1.0.0-beta  
**Snapshot Date:** 2026-09-09  
**Status:** Official Research Beta Snapshot (Windows)

---

## Phase 1.5 — Honest Citations + Live KB Folder Watcher *(branch: phase-1.5-citations-and-gkb-sync)*

### A. Citations — page / section locators

- **PDF**: Source headers now show `filename (Page N)` using the 1-indexed PDF page number stored in Chroma metadata.
- **DOCX**: Parser groups paragraphs by heading style (Heading 1/2, Title). Each group emits a `Section: 'Title' ChunkN` locator — no invented paragraph numbers.
- **TXT / MD / HTML / CSV / JSON**: Each semantic chunk carries a `Chunk N` locator.
- **Images**: Vision-described images carry an `Image` locator.
- All locators flow from `rag_service.py` (workspace RAG) and `kb_service.py` (personal KB indexer) into Chroma metadata, then through `_build_citation_label()` in `chat.py` into the LLM context window and the `X-WS-Sources` / `X-KB-Sources` response headers.
- Source headers in the UI now display `filename (Page 4)` instead of bare filenames.
- WS and KB source labels are delimited with `|` (not `,`) in HTTP headers to avoid ambiguity with locator text that may itself contain commas.

### B. Global Knowledge Base — Real Windows folder mapping & interval-poll sync

- **Windows folder mapping (Phase 1.5B)**:
  - The native Windows launcher (`start.exe`) allows mapping local Windows folders via `start.exe --add-folder` or the `[A]` command.
  - When a folder is mapped, the launcher copies files into `./knowledge_base_data/<slug>/` using a one-way `robocopy /E` background process (`/MON:1 /MOT:1`).
  - The initial copy pass completes synchronously before indexing begins.
  - Changes in a mapped Windows folder appear within about one minute (robocopy `/MOT:1` plus KB poll interval). Not a live, continuous, or kernel watcher.
  - Raw user files on Windows are never deleted or modified. Existing files in destination outside the source tree are preserved.
- **Explicit rejection of Windows paths in UI**:
  - The web UI detects Windows paths (e.g. `C:\...`) and prevents submission, explaining the launcher mirror workflow.
  - The backend returns HTTP 422 if a Windows path is sent directly, preventing un-indexable configurations.
  - Inaccessible paths log a `WARNING` in the watcher (no silent skipping at DEBUG level).
- **Supported KB file formats**:
  - Knowledge Base indexes: **PDF**, **DOCX**, **PNG**, **JPG**, **JPEG**, **TXT**, **MD**, **HTML**.
  - **CSV** and **JSON** are intentionally excluded from KB indexing until dedicated tabular chunkers are implemented (they remain supported in Workspace uploads).
- **Sync & Polling details**:
  - `KBService` background thread (`KB-Folder-Sync-Watcher`) polls active folders every `KB_AUTO_SYNC_INTERVAL_SECONDS` (default **30 s**, env-tunable).
  - **Detection mechanism**: `os.walk` + `os.path.getmtime` — **not** a kernel filesystem watcher. Changes are detected within the poll interval.
  - File-system changes are debounced for `KB_SYNC_DEBOUNCE_SECONDS` (default **3 s**) before triggering `sync_folder()`.
  - Overlap-safe via `_acquire_sync_lock()` — duplicate in-flight syncs are skipped.

---

## Overview

This is an official frozen research-beta snapshot of StarkLLM, designed for local-first privacy, document RAG, and personal knowledge base exploration using Docker and native Ollama on Windows.

---

## What Works

- **Clean Docker Startup**: Automatic database initialization on clean volume creation without Alembic schema collision.
- **Pre-Configured Environment**: Ready-to-run `.env` shipped directly in the distribution archive with secure research defaults.
- **Default Models**:
  - Chat / Completion: `qwen3.8:27b` (shipped `.env` default; `qwen2.5:7b` / `3b` for lightweight setups)
  - Document Embeddings: `qwen3-embedding:0.6b` (shipped `.env` default; `nomic-embed-text` alternative)
  - Vision (optional): `llava`
- **Robust Launchers (Phase 1 Hardened)**:
  - `start.exe`, `start.cmd`, and `start.bat` perform automated container cleanup before launch to prevent naming and port conflicts.
  - Preflight checks verify Docker Desktop engine status, WSL2 kernel availability, Ollama reachable on host, required local models, and free local ports (8000/5173).
  - Generates `preflight_report.txt` for instant diagnostic and support triage.
  - Launchers poll backend `/health` before launching the browser to eliminate HTTP 502 Bad Gateway race conditions.
- **Onboarding Wizard Resilience**: Exponential backoff and automated retry handling during backend container initialization.
- **Verified Packaging**: Complete standalone distribution ZIP with all frontend/backend source assets, launchers, and offline TTS models included.

---

## Required Host Software & Prerequisites

1. **Operating System**: Windows 10 / 11 with WSL2 enabled.
2. **Docker Desktop**: Installed and running in the system tray.
3. **Ollama**: Installed natively on Windows host from [ollama.com](https://ollama.com).
4. **Recommended Models**:
   ```bash
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text
   ```

---

## Known Limitations

- **Backup / Restore UI**: Full automated database and vector backup/restore UI is not yet implemented (manual volume backups supported).
- **TTS Languages**: High-quality local Piper TTS models are included for English and German; Persian/Arabic TTS is not yet supported.
- **Web Search**: Optional live external web search toggle is not integrated; all queries operate exclusively on local documents and knowledge base.
- **Indexing Progress**: Real-time per-chunk indexing progress indicators in the Knowledge Base UI are basic.
- **Authentication Key**: The `SECRET_KEY` included in the default `.env` is a research default intended for local single-user research installations. Change it in `.env` if exposing on local network.

---

## Disclaimer

StarkLLM is provided "as is" as an open-source Research Beta without commercial warranty or SLA.

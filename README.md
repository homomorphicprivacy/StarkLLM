# StarkLLM (Windows Research Beta)

**Version:** StarkLLM v1.0.0-beta  
**License:** Apache 2.0 (Open Source)  
**Package SHA-256:** `15aa772d586946af5213dd9a0f74bcf725f87cd15502d23e48cfc8d1e128fb43`

**StarkLLM** is a private, local-first AI assistant designed for Windows developers, researchers, and technical users. It is **completely free** and **open source** under Apache 2.0. It features an integrated Retrieval-Augmented Generation (RAG) engine, allowing you to chat with your local documents, organize workflows into Workspaces, and maintain a global Knowledge Base—all running entirely on your own hardware.

By leveraging Docker Desktop and Ollama, StarkLLM enforces a strict zero-cloud architecture. Your files and chats never leave your machine.

---

## Requirements

To run StarkLLM smoothly, you need:
- **OS**: Windows 10/11 (with WSL2 enabled)
- **Software**: 
  - **Docker Desktop** (running and configured for WSL2)
  - **Ollama** (installed natively on your Windows host from [ollama.com](https://ollama.com))
- **Hardware**:
  - **Minimum**: 8 GB RAM (for 3B models such as `qwen2.5:3b`)
  - **Recommended**: 16 GB+ System RAM, NVIDIA GPU with 8GB+ VRAM (for 7B models such as `qwen2.5:7b`)
  - **Storage**: Fast SSD with at least 30GB free space for containers and model weights.

---

## Recommended Models

Before launching StarkLLM, open PowerShell or Command Prompt and pull the recommended local models:

```bash
# Recommended default text generation model (7B)
ollama pull qwen2.5:7b

# Document embedding model (Required for RAG)
ollama pull nomic-embed-text
```

*Optional alternative models:*
- Lightweight / 8GB RAM laptops: `ollama pull qwen2.5:3b`
- High-capacity / 16GB+ VRAM power users: `ollama pull qwen2.5:14b`
- Multimodal / Vision models: `ollama pull llava`

---

## Starting and Stopping StarkLLM

### First-Run Sequence

1. **Start Docker Desktop**: Ensure Docker Desktop is running in your Windows system tray.
2. **Pull Ollama Models**: Run `ollama pull qwen2.5:7b` and `ollama pull nomic-embed-text`.
3. **Download & Extract ZIP**: Extract `StarkLLM-v1.0.0-beta.zip` to a local folder (e.g. `C:\StarkLLM\`).
4. **Open Terminal in folder**: In File Explorer, click the address bar, type `cmd` (or `powershell`), and press **Enter**.
5. **Run Launcher**:
   - Primary: Run `start.exe` (or in PowerShell: `.\start.exe`). If Windows SmartScreen displays a warning, click **More info** → **Run anyway**.
   - Fallback: Run `start.cmd`
   - Last resort: `docker compose up --build -d`
   *(Optional unblock helper if execution policies restrict scripts: `powershell -ExecutionPolicy Bypass -File unblock.ps1`)*
6. **Open StarkLLM**: Navigate to `http://localhost:5173` in your browser.

---

## Verification & Integrity

To verify the integrity of your downloaded release archive, run in PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 StarkLLM-v1.0.0-beta.zip
```
Expected SHA-256 digest: `15aa772d586946af5213dd9a0f74bcf725f87cd15502d23e48cfc8d1e128fb43`

---

## First-Use Flow

1. **Login**: Create a local account upon opening the interface. Authentication is 100% local, backed by SQLite.
2. **Create a Workspace**: Organize research into distinct workspaces (e.g., "Legal Analysis" or "Codebase Review").
3. **Upload Documents**: Drag and drop supported files (PDF, DOCX, TXT, MD, CSV, JSON, HTML) into the active workspace.
4. **Knowledge Base**: Map a permanent local Windows folder to index files globally across all chat sessions.

---

## Important Notes & Legal

**Research Beta & Local-First**  
This is a **Research Beta** release for Windows. It operates entirely local-first and is open source under Apache 2.0.

**Disclaimer (No Warranty / No Liability)**  
The software is provided "as is", without warranty of any kind, express or implied. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability arising from, out of, or in connection with the software.

---

## Contact & Links

- **Website**: [https://starkllm.com](https://starkllm.com)
- **GitHub**: [https://github.com/homomorphicprivacy/StarkLLM](https://github.com/homomorphicprivacy/StarkLLM)
- **Contact**: info@starkllm.com
- **Creator**: Christian Stark — Maxstr. 14, 52070 Aachen, Germany

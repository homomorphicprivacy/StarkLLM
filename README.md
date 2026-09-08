# StarkLLM (Research Beta)

**StarkLLM** is a private, local-first AI assistant designed for developers and technical users. It is **completely free** and **open source**, intended for research and non-commercial use. It features an integrated Retrieval-Augmented Generation (RAG) engine, allowing you to chat with your local documents, organize workflows into Workspaces, and maintain a global Knowledge Base—all running entirely on your own hardware. 

By leveraging Docker and Ollama, StarkLLM keeps your data completely secure. Your files and chats never leave your machine.

---

## Requirements

To run StarkLLM smoothly, you need:
- **OS**: Windows 10/11 (with WSL2 enabled)
- **Software**: 
  - **Docker Desktop** (running and configured for WSL2)
  - **Ollama** (installed natively on your Windows host)
- **Hardware**:
  - An NVIDIA GPU with at least 8GB VRAM is strongly recommended for running 27B parameter models.
  - 16GB+ System RAM.
  - SSD storage for fast document indexing and retrieval.

---

## Setup & Installation

1. **Clone or Extract** the StarkLLM repository to your local machine.
2. **Install Ollama** from [ollama.com](https://ollama.com) and ensure it is running in your system tray.
3. **Open your Terminal** (Command Prompt or PowerShell) and pull the required models:
   ```bash
   # Core text generation model
   ollama pull qwen3.6:27b

   # Document embedding model (Required for RAG)
   ollama pull qwen3-embedding:0.6b

   # Vision model (if utilizing image uploads)
   ollama pull llava
   ```
4. **Ensure Docker Desktop is running**.

---

## Starting and Stopping StarkLLM

### Official First-Run Sequence

1. **Start Docker Desktop**: Ensure Docker Desktop is installed and running in your system tray.
2. **Install Ollama & pull models**:
   ```bash
   ollama pull qwen3.6:27b
   ollama pull qwen3-embedding:0.6b
   ```
3. **Download & Extract ZIP**: Extract the package completely to a folder (e.g. `C:\StarkLLM\`).
4. **Open Terminal in folder**: In File Explorer inside the extracted folder, click the address bar, type `cmd`, and press **Enter**.
5. **Run Launcher**:
   - Primary: Run `start.exe`. If Windows SmartScreen displays a warning, click **More info** → **Run anyway**.
   - Fallback: Run `start.cmd`
   - Last resort: `docker compose up --build -d`
   *(Optional unblock helper if scripts are restricted: `powershell -ExecutionPolicy Bypass -File unblock.ps1`)*
6. **Open StarkLLM**: Navigate to `http://localhost:5173` in your browser.

---

## First-Use Flow

1. **Login**: Upon opening StarkLLM, create a local account. (Auth is local-only, backed by SQLite).
2. **Create a Workspace**: Your starting point. Name it after a project (e.g., "Research Project").
3. **Upload Documents**: Click the '+' icon next to the chat bar to upload PDFs or TXTs to the current Workspace. You can track the progress directly in the UI.
4. **Knowledge Base**: Navigate to the Knowledge Base view via the sidebar. Follow the instructions in the UI helper to manage your files.

### Knowledge Base Folder Guidance
To make managing global files easier, a specific folder on your Windows machine is mapped directly into StarkLLM. 
- Go to the **Knowledge Base** page in the app.
- Check the **"Where do I put my files?"** helper box. It will provide the exact Windows folder path you should use.
- Copy that path, open it in Windows Explorer, and drop your documents there.
- Return to StarkLLM and click **Add Folder** (or **Register Root Folder Now**) to scan and index them for chatting.

---

## Important Notes & Legal

**Research Beta & Local-First**
This is a **Research Beta** release for Windows. It operates entirely local-first and is completely **open source**, allowing you to inspect and modify the code.

**Free / Non-Commercial Use**
StarkLLM is **completely free** and provided for **non-commercial research use** only. 

**Disclaimer (No Warranty / No Liability)**
The software is provided "as is", without warranty of any kind, express or implied. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability arising from, out of, or in connection with the software or the use or other dealings in the software.

---

## Contact & Credits

- **Website**: [https://starkllm.com](https://starkllm.com)
- **Contact**: info@starkllm.com
- **Creator**: Christian Stark
- **Location**: Maxstr. 14, 52070 Aachen

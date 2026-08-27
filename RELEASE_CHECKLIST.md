# StarkLLM Release Checklist

Before packaging or publishing a new Research Beta release for Windows, manually verify the following core workflows to ensure stability.

### 1. Environment & Setup
- [ ] **Launcher**: Run `start.bat` Option 1. Verify that Docker Compose builds/starts successfully.
- [ ] **Browser Launch**: Verify that `http://localhost:5173` opens automatically.

### 2. Core Workflows
- [ ] **Login**: Create a new local account and log in successfully.
- [ ] **Workspaces**: Create a new Workspace and verify it appears in the sidebar.
- [ ] **PDF Upload**: Upload a test PDF into the Workspace. Verify it processes (extracts, chunks, embeds) without a 413/500 error.
- [ ] **Chat with Document**: Ask a question about the uploaded PDF. Verify the RAG engine retrieves context and streams a valid response.

### 3. Knowledge Base
- [ ] **Windows UX Helper**: Navigate to the Knowledge Base page. Verify the "Where do I put my files?" helper box displays the correct absolute Windows path.
- [ ] **Scan/Index**: Add a folder, drop a file into the mapped directory, click Sync/Index, and verify the file status turns to "Indexed".

### 4. UI & Branding Consistency
- [ ] **About Page**: Open Settings > About StarkLLM. Verify the legal text (No Warranty), Christian Stark, Maxstr. 14, 52070 Aachen, and Research Beta tags are correct.
- [ ] **Free & Open Source Wording**: Verify that "completely free" and "open source" are explicitly stated in both the `README.md` and the in-app About page.

### 5. Shutdown
- [ ] **Graceful Stop**: Run `start.bat` Option 2. Verify all Docker containers shut down cleanly.

Once all steps are marked as successful, the build is ready for release!

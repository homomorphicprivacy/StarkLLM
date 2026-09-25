# Phase 1.5 — Manual Verification Checklist (Windows)

Branch: `phase-1.5-citations-and-gkb-sync`

Run these checks **in order** after `start.exe` completes and the browser opens at
`http://localhost:5173`.

---

## Check 1 — PDF page citation in UI source chips

**Setup**
1. Create or open a Workspace.
2. Upload a multi-page PDF (any PDF with >= 3 pages of text).
3. Wait for the "indexed" status to appear.
4. Ask a question whose answer is on a known page (e.g. page 2).

**Expected UI text** (source chips below the assistant reply):

```
Workspace: yourfile.pdf (Page 2)
```

Not acceptable: `Workspace: yourfile.pdf` (bare filename only).

**Expected LLM context** (visible in Docker logs with `docker logs starkllm-backend`):

```
[Document: yourfile.pdf (Page 2)]
```

---

## Check 2 — DOCX section heading citation

**Setup**
1. Upload a DOCX file that has at least one paragraph styled as **Heading 1** or
   **Heading 2** in Microsoft Word (or LibreOffice with explicit heading styles).
2. Ask a question whose answer falls under that heading.

**Expected UI text**:

```
Workspace: yourdoc.docx (Section: 'Introduction' chunk 1)
```

Not acceptable:
- `yourdoc.docx (Paragraph 3)` — invented paragraph numbers are banned.
- `yourdoc.docx (Chunk 1)` only — section name must appear if a heading was found.

If the DOCX has **no heading styles**, the fallback is acceptable:

```
yourdoc.docx (Chunk 1)
```

---

## Check 3 — Pipe-delimited source headers (regression check)

**Setup**
Upload two documents and ask a question that retrieves chunks from both.

**Expected**: both sources appear as separate chips in the UI.

**Verify in browser DevTools -> Network -> the streaming chat response**:
- `X-WS-Sources` header value must use `|` as separator, e.g.:
  `file-a.pdf%20(Page%201)|file-b.docx%20(Section...)`
- Must NOT use `,` inside a single label.

---

## Check 4 — Real Windows folder mapping via launcher (`start.exe`)

**Setup**
1. Create a test folder on your Windows host (e.g. `C:\Users\<user>\Documents\test_research`).
2. Run `start.exe` in terminal.
2. Run `start.exe --add-folder` in terminal (or press `[A]` in the running launcher).
3. Select `test_research` in the native Windows folder picker.
4. `start.exe` runs a one-way copy into `knowledge_base_data\test-research\`, starts background sync (`/MON:1 /MOT:1`), and registers `/kb_data/test-research`.
5. Drop a PDF, TXT, or MD file into `C:\Users\<user>\Documents\test_research\`.
6. Wait about one minute (robocopy `/MOT:1` 1-minute idle check + container watcher poll). Changes appear within about one minute — this is interval polling, not a continuous kernel watcher.

**Expected**:
- File appears in `knowledge_base_data\test-research\`.
- Docker logs show:
```
KB Watcher: Change detected in folder ID N ('/kb_data/test-research'). Will sync after 3s debounce.
KB Watcher: Debounce expired for folder ID N. Triggering auto-sync.
```
- In Knowledge Base UI (`http://localhost:5173`), the folder appears with the file status **indexed**.

---

## Check 5 — Web UI rejects Windows paths with helpful guidance

**Setup**
1. In the StarkLLM UI -> Knowledge Base -> Click **Add Folder** -> **Enter path manually**.
2. Type a Windows host path, e.g. `C:\Users\chris\Documents`.

**Expected UI response**:
- The input border turns red.
- A warning banner appears immediately:
  `Windows path detected. Paths like C:\Users\... are not visible inside the Docker container... Use the StarkLLM launcher instead...`
- The **Add Folder** submit button is disabled.
- Submitting directly via API returns HTTP 422 with a descriptive error message.

---

## Check 6 — Overlap safety: no double-sync

**Setup**
1. Drop a large file into the mapped folder.
2. Immediately click **Sync now** in the UI while indexing is in progress.

**Expected Docker log**:
```
KB: Sync for folder ID N is already in progress. Skipping duplicate request.
```

No duplicate indexing run should start.

---

## Summary table

| # | Feature | Pass condition |
|---|---------|---------------|
| 1 | PDF page citation | `filename (Page N)` in source chip |
| 2 | DOCX section citation | `filename (Section: 'X' chunk N)` when heading exists |
| 3 | Pipe delimiter | `|` in X-WS-Sources header, not `,` inside a label |
| 4 | Windows folder mapping | Selected via `start.exe`, mirrored by robocopy, indexed automatically |
| 5 | Windows path rejection | UI warns and disables submit; API returns 422 |
| 6 | Overlap safety | Second sync skipped with log message |

---

## What is NOT verified here (still marketing-only)

The following website copy makes claims that no code in this branch fulfils.
These are tracked for future sprints and must NOT be described as implemented.

| Location | Claim | Reality |
|----------|-------|---------|
| website/product.html:65 | "link directly to the underlying source **paragraphs**" | Citations go to page/section/chunk — not paragraph-level spans |
| website/product.html:87 | "**Continuous Synchronization**: As you add or modify files ... the Knowledge Base updates" | Sync happens within the poll interval (default 30s), container-visible paths only |
| website/tech-rag.html:57 | "searches ... for **paragraphs** semantically related" | Chunks are variable-size semantic chunks, not guaranteed paragraph units |

> The website files (website/) are a Git submodule. Do not edit them unless
> explicitly instructed — changes require a separate commit to the submodule repo.

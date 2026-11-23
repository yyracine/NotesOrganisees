# AGENTS.md

## Project

Flask web app that structures raw meeting notes with DeepSeek (OpenAI-compatible) and exports PDF/DOCX. Vanilla HTML/CSS/JS frontend (no build step). Python 3.15.

## Commands

- Install: `pip install -r requirements.txt`
- Run app: `python app.py` → http://127.0.0.1:5000 (debug mode)
- API smoke test: `python main.py` (minimal DeepSeek call)
- No test suite, linter, or typechecker is configured. Verify changes manually via the running app.

## Environment

- `.env` (gitignored) must define `DEEPSEEK_BASE_URL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`. Template: `.env.example`.
- `DEEPSEEK_API_KEY` placeholder check: `app.py` rejects the literal `your_deepseek_api_key_here`.
- DeepSeek call uses `response_format: {"type": "json_object"}`; SYSTEM_PROMPT demands strict JSON. `parse_json()` also strips markdown fences as a fallback.

## Key files

- `app.py` — Flask routes + AI call + PDF/DOCX builders + file import extraction.
- `templates/index.html`, `static/style.css`, `static/app.js` — UI.
- `opencode.json` — MCP server `document-generator` (local, `npx -y document-generator-mcp@latest`, Node 18+).
- `main.py` — standalone API example.

## Routes

- `GET /` — UI
- `POST /api/organize` — `{notes}` → `{data, raw}`
- `POST /api/pdf` — `{data}` → PDF
- `POST /api/docx` — `{data}` → DOCX
- `POST /api/import` — multipart `file` → `{text, filename}`

## Import constraints

- Allowed extensions: `.txt .md .csv .log .json .docx .pdf`
- Max size: 5 MB (`MAX_UPLOAD_BYTES`). Empty files rejected.
- Text decoded UTF-8 → UTF-8-sig → latin-1 → cp1252. DOCX via python-docx (paragraphs + tables). PDF via pypdf.

## PDF/DOCX gotchas

- fpdf2 core fonts are latin-1. `_safe()` re-encodes with `latin-1` replace; non-Latin-1 chars become `?`. Do not pass raw unicode to `pdf.cell`/`multi_cell` without `_safe`.
- `build_docx` uses `python-docx` (imported as `_docx_mod`); `_extract_text` uses the same module as `_docx`.
- `python-docx` is imported twice (`_docx` and `_docx_mod`) — consolidate if refactoring.
- `WD_ALIGN_PARAGRAPH` / `Pt` imported but unused; harmless.

## UI conventions

- Theme: `data-theme` on `<html>`, persisted in `localStorage`, defaults to `prefers-color-scheme`. `themeColorMeta` updated alongside.
- Status elements need `aria-live="polite"` (already on `#status`, `#importStatus`).
- Loading state: `.btn.loading` adds spinner; toggle via `setLoading(btn, bool)`.
- Destructive reset requires `confirm()`.

## Gitignored

`.env`, `__pycache__/`, `*.pyc`, `.venv/`, `.npx-cache/`, `generated_documents/` are gitignored. `DOCUMENTATION.docx`/`.pdf` at root are committed generated docs. Do not commit real API keys.

## MCP

- `opencode.json` registers `document-generator`. Tools: `gerar_documento_pdf`, `gerar_documento_word`. Templates: professional/minimalist/corporate/default. Formats: word/pdf/ambos.
- Generated files land in `./generated_documents/`.
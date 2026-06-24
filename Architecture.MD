# Markly — Architecture Overview

## Project Status
Lean monolithic MVP in product-market fit validation phase. Single-app Panel project, no packaging, no tests, no CI.

---

## Module Map

| File | Role | Dependencies |
|------|------|-------------|
| `app.py` | Panel UI — widgets, layout, event wiring | All other modules |
| `engine.py` | AI pipeline — subject detection, grading, image markup, model racing | `personas.py`, `rubrics.py` |
| `markup.py` | Red-pen image annotations via PIL | `fonts/` (Caveat, PatrickHand) |
| `report.py` | PDF report generation via reportlab | `markup.py` |
| `storage.py` | Student history CRUD against `students.json` | None |
| `utils.py` | File ingestion — PDF (fitz), DOCX (python-docx), images (Tesseract) | External tools |
| `personas.py` | Per-subject teacher prompt templates | None |
| `rubrics.py` | Scoring rubrics (Math, English, Science, Programming) | None |
| `install_fonts.py` | Downloads Google Fonts into `fonts/` | None |

---

## Data Flow

```
Teacher Uploads Assignment
         │
         ▼
┌─────────────────────┐
│    utils.py         │  PDF → fitz, DOCX → python-docx, Image → Tesseract OCR
│  (file ingestion)   │
└─────────┬───────────┘
          │ text content
          ▼
┌─────────────────────┐
│   engine.py         │  Calls OpenRouter → detects subject → selects rubric
│ (subject detection) │
└─────────┬───────────┘
          │ detected subject
          ▼
┌─────────────────────┐
│   engine.py         │  Grades text via AI → structured feedback + score
│  (text grading)     │
└─────────┬───────────┘
          │ grade + feedback
          ├─────────────────────────────────┐
          ▼                                 ▼
┌─────────────────────┐          ┌─────────────────────┐
│   storage.py        │          │  engine.py          │  For image subs: sends
│  (save to JSON)     │          │ (image grading)     │  screenshot+rubric to AI
└─────────────────────┘          └─────────┬───────────┘
                                            │ markup params
                                            ▼
                                   ┌─────────────────────┐
                                   │   markup.py         │  PIL draws annotations
                                   │ (annotation render) │  using handwriting fonts
                                   └─────────┬───────────┘
                                             │ annotated image
                                             ▼
                                   ┌─────────────────────┐
                                   │   report.py         │  reportlab generates
                                   │  (PDF generation)   │  annotated PDF report
                                   └─────────────────────┘
```

---

## AI Pipeline (`engine.py`)

### Architecture
- All AI calls go through **OpenRouter** (`https://openrouter.ai/api/v1`) as the gateway
- Uses `AsyncOpenAI` client — OpenRouter is OpenAI-compatible
- **Model racing**: multiple AI models queried concurrently via `asyncio.gather`; first successful result wins

### Pipeline Stages
1. **Subject Detection** — sends document text to OpenRouter, asks it to classify as Math/English/Science/Programming
2. **Rubric Selection** — loads the matching rubric from `rubrics.py`
3. **Teacher Persona** — loads the matching persona from `personas.py`
4. **Text Grading** — sends rubric + persona + document text for structured evaluation
5. **Image Grading** — for image submissions: sends screenshot + rubric to vision-capable model, returns markup parameters

### Critical Issues
- `AsyncOpenAI` client is created at **module import time** (`engine.py:21-23`). If `.env` is missing or the API key is invalid, the module crashes on import before any code runs.
- **No error handling, retry logic, or fallbacks** around any AI API call. Network failures, rate limits, or model errors bubble up as unhandled exceptions.
- The `API_KEY` environment variable is read at import time with no validation or user-friendly error.

---

## Annotation System (`markup.py`)

### Rendering
- Uses **Pillow (PIL)** to draw annotations directly on assignment images
- Handwriting-style fonts: Caveat (Regular, Bold) and Patrick Hand
- Fonts must be pre-installed via `install_fonts.py` into `fonts/`

### Annotation Types
- ✅ Correct-answer ticks (green)
- ❌ Incorrect-answer crosses (red)
- Circles around errors
- Teacher comments in margins
- Corrections and suggestions
- Encouragement remarks
- Summary feedback block

### Fallback Chain
1. `fonts/` directory checked first
2. Falls back to system fonts at Linux paths (`/usr/share/fonts/...`)
3. Final fallback: PIL default font (italic serif)

### Issue
- Font fallback references **Linux-specific paths** — will fail on Windows or macOS without those fonts present.
- Uses `random` jitter for hand-drawn positioning — annotations are **non-reproducible**, making testing impossible without mocking `random`.

---

## Persistence (`storage.py`)

### Storage
- Flat **`students.json`** file — auto-created on first write
- Keyed by student name → array of history entries
- Each entry: `{ subject, grade, feedback, timestamp }`

### Pattern
```
load_db() → modify in memory → save_db()
```

### Critical Issues
- **Not thread-safe**. Under concurrent Panel sessions, simultaneous `save_db()` calls can interleave and corrupt data.
- **PII leakage**: Contains real student names, grades, and feedback. Tracked in git — **not in `.gitignore`**. No encryption or access control.
- No schema validation on read/write.
- Not a proper database — no querying, no indexing, no atomicity.

---

## File Ingestion (`utils.py`)

| Format | Library | Method |
|--------|---------|--------|
| PDF | PyMuPDF (`fitz`) | Extract text page by page |
| DOCX | `python-docx` | Extract paragraphs |
| Image (PNG/JPG) | Tesseract OCR | Extract text via `pytesseract` |
| Image → base64 | Built-in | `base64.b64encode` for AI API |

### Issues
- `image_to_base64` is misplaced here — it's used by the AI image grading pipeline, not file ingestion. Should live in `engine.py` or a shared utility.
- Tesseract OCR is a **system-level dependency** — must be installed globally with binary in PATH. No fallback if missing.
- No file size validation, format validation, or sanitization.

---

## PDF Report Generation (`report.py`)
- Uses **reportlab** to generate downloadable PDFs
- Contains: student info, subject, grade, strengths, improvements, teacher comments, annotated pages
- Output is designed for sharing with students/parents/admins

---

## UI Layer (`app.py`)

### Stack
- **Panel** — no React/Vue, pure Python reactive UI
- Designed for **Hugging Face Spaces** deployment
- `panel serve app.py` for local or hosted

### Architecture
- Inline CSS (no separate stylesheets)
- Widget definitions + callback wiring in a single file
- Business logic invoked directly from UI callbacks

### Issues
- **Mixed concerns**: CSS, widget definitions, callback logic, and UI state management all in one file.
- No `__main__` guard — `python app.py` may not work (designed for `panel serve`).
- No loading/error states visible for async operations (Panel handles some of this natively, but long-running AI calls could benefit from progress indicators).

---

## Cross-Cutting Concerns

### Security
| Risk | Severity | Details |
|------|----------|---------|
| API key at import time | High | `engine.py` reads `OPENROUTER_API_KEY` at module level — crashes if missing |
| No API error handling | High | Any AI call failure propagates as unhandled exception |
| PII in git | High | `students.json` with names/grades committed, not in `.gitignore` |
| No input validation | Medium | Uploaded files not validated for size, type, or content |
| No rate limiting | Medium | No protection against abuse in hosted deployment |

### Reliability
| Risk | Severity | Details |
|------|----------|---------|
| Thread-unsafe storage | High | Concurrent Panel sessions can corrupt `students.json` |
| No retry on AI calls | High | Network blips cause total failure |
| Tesseract hard dependency | Medium | App crashes if OCR not installed |
| Font dependency | Medium | Runtime crash if `fonts/` missing |

### Maintainability
| Issue | Details |
|-------|---------|
| No `__init__.py`, `setup.py`, `pyproject.toml` | Imports work by path, not packaging |
| No tests | No coverage, no test framework |
| No linting/type checking | No `.ruff.toml`, `.mypy.ini`, or `pyproject.toml` |
| No CI/CD | No `.github/` workflows |
| Module-level side effects | `engine.py` creates AI client at import time |
| Mixed concerns in `engine.py` | Subject detection, grading, image markup in one ~300+ line module |

---

## Dependencies

52 packages in `requirements.txt`. Key dependencies:

| Package | Purpose |
|---------|---------|
| `panel` | UI framework |
| `openai` (AsyncOpenAI) | OpenRouter AI client |
| `PyMuPDF` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `pytesseract` | OCR for images |
| `Pillow` | Image annotation rendering |
| `reportlab` | PDF report generation |
| `python-dotenv` | `.env` loading |
| `aiofiles` | Async file I/O |

---

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│           Hugging Face Spaces           │
│  ┌───────────────────────────────────┐  │
│  │  panel serve app.py              │  │
│  │  ┌─────┐ ┌───────┐ ┌──────────┐ │  │
│  │  │ UI  │→│Engine │→│Storage   │ │  │
│  │  │     │ │       │ │(JSON)    │ │  │
│  │  └─────┘ └───┬───┘ └──────────┘ │  │
│  │              ▼                   │  │
│  │       OpenRouter                 │  │
│  │       (AI Gateway)               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

No containerization, no database, no CDN. Single-process Panel app behind HF Spaces proxy.

---

## Recommendations (Priority Order)

1. **Lazy-init AsyncOpenAI client** in `engine.py` — wrap in function with try/except, validate key at first use not import
2. **Add error handling + retry** around all AI API calls — exponential backoff, model fallback list
3. **Make `storage.py` thread-safe** — file locking (`filelock` or `fcntl`) or switch to SQLite
4. **Add `students.json` to `.gitignore`** — prevent PII from entering version control
5. **Fix font fallback in `markup.py`** — use `fonts/` only, or detect platform for system font paths
6. **Split `engine.py`** into separate modules: `detector.py`, `grader.py`, `imarker.py`
7. **Add `__main__` guard to `app.py`**
8. **Seal the layout**: add `pyproject.toml` with project metadata and entry point

# Markly — Architecture Overview

**Project:** Markly — AI-Powered Assignment Grading & Feedback System  
**Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Active Development  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Context (C4 Level 1)](#2-system-context-c4-level-1)
3. [Container Diagram (C4 Level 2)](#3-container-diagram-c4-level-2)
4. [Component Diagram (C4 Level 3)](#4-component-diagram-c4-level-3)
5. [Module Deep-Dives](#5-module-deep-dives)
6. [Data Flow](#6-data-flow)
7. [Technology Stack](#7-technology-stack)
8. [External Dependencies](#8-external-dependencies)
9. [Data Stores](#9-data-stores)
10. [Security Architecture](#10-security-architecture)
11. [Deployment & Infrastructure](#11-deployment--infrastructure)
12. [Development Environment](#12-development-environment)
13. [Architectural Decisions](#13-architectural-decisions)
14. [Future Considerations](#14-future-considerations)
15. [Glossary](#15-glossary)

---

## 1. Project Overview

Markly is a Python-based web application that automates the grading and feedback of student assignments using AI. Teachers upload assignments (PDF, DOCX, or images), and the system:

1. Extracts text from the uploaded files
2. Sends content to AI models via the OpenRouter API for assessment
3. Generates teacher-style visual annotations (handwritten marks, ticks, crosses, margin notes) on assignment images
4. Produces a two-page PDF report (annotated image + structured feedback)
5. Persists grading history in a JSON flat-file database

The system is designed as a single-user or small-team tool, prioritizing simplicity and rapid deployment over enterprise scalability.

---

## 2. System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Markly System                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │   [Teacher/User] ────────► [Markly Web Application]         │   │
│  │        │                           │                        │   │
│  │        │                           │                        │   │
│  │        │                    Uploads assignments              │   │
│  │        │                    Reviews feedback                 │   │
│  │        │                    Downloads PDF reports            │   │
│  │        │                           │                        │   │
│  │        └─────── Receives annotated PDFs & feedback ◄───────┘   │
│  │                                                             │   │
│  │                           │                                 │   │
│  │                           ▼                                 │   │
│  │              [OpenRouter AI API]                            │   │
│  │              (External AI Inference Service)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Primary Actor:** Teacher — uploads assignments, reviews AI-generated feedback, downloads reports.  
**External System:** OpenRouter API — provides access to multiple LLM models (GPT-4, Claude, etc.) for grading.

---

## 3. Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Markly Application                              │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐      │
│  │                 │    │                  │    │                     │      │
│  │   Panel Web UI  │◄──►│  Python Backend  │◄──►│  OpenRouter Client  │      │
│  │   (app.py)      │    │  (Core Pipeline) │    │  (engine.py)        │      │
│  │                 │    │                  │    │                     │      │
│  │  • File Upload  │    │  • Orchestration │    │  • Model Racing     │      │
│  │  • Form Inputs  │    │  • State Mgmt    │    │  • Subject Detect   │      │
│  │  • Results View │    │  • Error Handling│    │  • Prompt Assembly  │      │
│  │  • PDF Download │    │                  │    │                     │      │
│  └─────────────────┘    └────────┬─────────┘    └─────────────────────┘      │
│           │                      │                                          │
│           │                      ▼                                          │
│           │           ┌──────────────────┐    ┌─────────────────────┐       │
│           │           │                  │    │                     │       │
│           │           │  File Processing │    │  Visual Annotation  │       │
│           │           │  (utils.py)      │    │  (markup.py)        │       │
│           │           │                  │    │                     │       │
│           │           │  • PDF Extract    │    │  • Ticks/Crosses    │       │
│           │           │  • DOCX Extract   │    │  • Circles/Boxes    │       │
│           │           │  • OCR (Images)   │    │  • Margin Notes     │       │
│           │           │  • Base64 Encode  │    │  • Score Stamps     │       │
│           │           │                  │    │  • Summary Blocks   │       │
│           │           └──────────────────┘    └─────────────────────┘       │
│           │                      │                    │                     │
│           │                      ▼                    ▼                     │
│           │           ┌──────────────────┐    ┌─────────────────────┐       │
│           │           │                  │    │                     │       │
│           │           │  PDF Generation  │    │  JSON Storage       │       │
│           │           │  (report.py)     │    │  (storage.py)       │       │
│           │           │                  │    │                     │       │
│           │           │  • Two-page PDF  │    │  • students.json    │       │
│           │           │  • Metadata Table│    │  • History Tracking │       │
│           │           │  • Text Reports  │    │  • Atomic Writes    │       │
│           │           │                  │    │                     │       │
│           │           └──────────────────┘    └─────────────────────┘       │
│           │                      │                                          │
│           └──────────────────────┘                                          │
│                     (Results displayed in UI)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────────┐
              │         External Systems            │
              │                                     │
              │  ┌─────────────┐  ┌─────────────┐  │
              │  │             │  │             │  │
              │  │  OpenRouter │  │  Tesseract  │  │
              │  │  AI API     │  │  OCR Engine │  │
              │  │  (HTTPS)    │  │  (System)   │  │
              │  │             │  │             │  │
              │  └─────────────┘  └─────────────┘  │
              │                                     │
              │  ┌─────────────┐  ┌─────────────┐  │
              │  │             │  │             │  │
              │  │  Google     │  │  Local      │  │
              │  │  Fonts CDN  │  │  Fonts Dir  │  │
              │  │  (HTTPS)    │  │  (fonts/)   │  │
              │  │             │  │             │  │
              │  └─────────────┘  └─────────────┘  │
              └─────────────────────────────────────┘
```

---

## 4. Component Diagram (C4 Level 3)

### 4.1 Core Pipeline Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python Backend (app.py)                            │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐      │
│  │  UI Controller  │    │  Grading Service │    │  Report Service     │      │
│  │                 │    │                  │    │                     │      │
│  │  • Widget Mgmt  │    │  • Pipeline Orch │    │  • PDF Assembly     │      │
│  │  • Event Handlers│   │  • State Machine │    │  • Image Scaling    │      │
│  │  • File Upload  │    │  • Error Recovery│    │  • Style Config     │      │
│  │  • Progress UI  │    │  • Result Caching│    │  • Buffer Mgmt      │      │
│  └────────┬────────┘    └────────┬─────────┘    └─────────────────────┘      │
│           │                      │                                          │
│           │                      ▼                                          │
│           │           ┌─────────────────────────────────────────┐            │
│           │           │         AI Engine (engine.py)           │            │
│           │           │                                         │            │
│           │           │  ┌─────────────┐  ┌─────────────┐     │            │
│           │           │  │             │  │             │     │            │
│           │           │  │  Subject    │  │  Model      │     │            │
│           │           │  │  Detector   │  │  Racer      │     │            │
│           │           │  │             │  │             │     │            │
│           │           │  │  • Content  │  │  • Parallel │     │            │
│           │           │  │    Analysis │  │    Requests │     │            │
│           │           │  │  • Keyword  │  │  • Response │     │            │
│           │           │  │    Matching │  │    Scoring  │     │            │
│           │           │  │  • Fallback │  │  • Consensus│     │            │
│           │           │  │             │  │             │     │            │
│           │           │  └─────────────┘  └─────────────┘     │            │
│           │           │                                         │            │
│           │           │  ┌─────────────┐  ┌─────────────┐     │            │
│           │           │  │             │  │             │     │            │
│           │           │  │  Prompt     │  │  Response   │     │            │
│           │           │  │  Builder    │  │  Parser     │     │            │
│           │           │  │             │  │             │     │            │
│           │           │  │  • Persona  │  │  • Grade    │     │            │
│           │           │  │    Selection│  │    Extract  │     │            │
│           │           │  │  • Rubric   │  │  • Markup   │     │            │
│           │           │  │    Assembly │  │    JSON     │     │            │
│           │           │  │  • Context  │  │  • Feedback │     │            │
│           │           │  │    Injection│  │    Text     │     │            │
│           │           │  │             │  │             │     │            │
│           │           │  └─────────────┘  └─────────────┘     │            │
│           │           └─────────────────────────────────────────┘            │
│           │                      │                                          │
│           │                      ▼                                          │
│           │           ┌─────────────────────────────────────────┐            │
│           │           │      External: OpenRouter API           │            │
│           │           │      (REST / JSON / HTTPS)              │            │
│           │           └─────────────────────────────────────────┘            │
│           │                                                                 │
│           └─────────────────────────────────────────────────────────────────┘
```

---

## 5. Module Deep-Dives

### 5.1 `utils.py` — File Ingestion & Processing

**Responsibility:** Extract text from uploaded files and prepare data for AI consumption.

| Function | Purpose | Key Dependencies |
|----------|---------|----------------|
| `extract_pdf(file_bytes)` | Extract text page-by-page from PDF | PyMuPDF (`fitz`) |
| `extract_docx(file_bytes)` | Extract paragraph text from DOCX | `python-docx` |
| `extract_image(file_bytes)` | OCR text extraction from images | `pytesseract` + Pillow |
| `extract_text_from_file(file_bytes, filename)` | Router/orchestrator based on file extension | All above |
| `image_to_base64(file_bytes)` | Encode images for AI API payload | `base64` |
| `extract_grade(text)` | Regex-based grade parsing from AI response | `re` |

**Design Decisions:**
- File type detection via extension (not MIME type) for simplicity
- In-memory processing only (no temp files) for security
- Regex grade extraction supports multiple formats: `X/10`, `Grade: A`, `X/100`

### 5.2 `markup.py` — Visual Annotation Engine

**Responsibility:** Render teacher-style handwriting annotations on assignment images using Pillow.

**Core Drawing Primitives:**

| Primitive | Function | Visual Effect |
|-----------|----------|---------------|
| Jitter | `_jitter(val, amount)` | Random ±2.5px offset for hand-drawn feel |
| Jittered Line | `_jittered_line()` | Segmented line with per-point noise |
| Wavy Underline | `_wavy_underline()` | Sinusoidal curve (amplitude=5, wavelength=14) |
| Wobbly Ellipse | `_wobbly_ellipse()` | Radius wobble (0.93–1.07x) + angle wobble |
| Rounded Rect | `_rounded_rect()` | Arc-based corners with fill/outline |
| Speech Bubble | `_speech_bubble()` | Auto-wrapped text with pointer |
| Tick | `_draw_tick()` | Three-segment checkmark |
| Cross | `_draw_cross()` | Two diagonal lines |
| Score Stamp | `_draw_score_stamp()` | Fractional score in circular format |
| Correction Box | `_draw_correction_box()` | Semi-transparent rounded rect + wavy underline |
| Margin Note | `_draw_margin_note()` | Wrapped text in side margins |
| Summary Block | `_draw_summary_block()` | Semi-transparent yellow feedback block |

**Key Design Patterns:**
- **Deterministic Randomness:** `random.seed(42)` ensures reproducible jitter
- **Font Caching:** `_FONT_CACHE` dict prevents repeated font loading
- **Alpha Layering:** Separate alpha channel for semi-transparent overlays

### 5.3 `report.py` — PDF Report Generation

**Responsibility:** Generate structured PDF reports using ReportLab.

**Two Report Types:**

| Type | Function | Use Case |
|------|----------|----------|
| Image + Text | `create_marked_pdf()` | Assignments with image pages |
| Text-Only | `create_pdf_report()` | Text-based assignments (DOCX, text-only PDF) |

**Page 1 Layout (Image Report):**
- Annotated assignment image scaled to A4 width
- Preserves aspect ratio

**Page 2 Layout (Image Report):**
- Metadata table (Student, Subject, File)
- Overall feedback paragraph
- Grade display
- Detailed corrections list

**Styling:**
- Uses `getSampleStyleSheet()` as base
- Custom `SmallMeta` style for metadata
- Table with fixed column widths (`38*mm` for labels)

### 5.4 `storage.py` — Persistence Layer

**Responsibility:** Read/write student grading history to `students.json`.

**Schema:**
```json
{
  "Student Name": {
    "history": [
      {
        "timestamp": "2026-06-26T00:00:00",
        "subject": "Math",
        "grade": "8/10",
        "feedback": "Detailed feedback text..."
      }
    ]
  }
}
```

**Operations:**
| Function | Behavior |
|----------|----------|
| `load_db()` | Returns `{}` if file missing or corrupted |
| `save_db(db)` | Atomic write with 2-space indentation |
| `add_record(student, subject, grade, feedback)` | Append to history, create student if new |
| `get_student_history(name)` | Returns formatted string or "No previous records." |

### 5.5 `engine.py` — AI Grading Pipeline (Architectural)

**Responsibility:** Orchestrate AI inference via OpenRouter.

**Pipeline Stages:**
1. **Subject Detection** — Analyze content to determine subject (Math, English, Science, Programming)
2. **Prompt Assembly** — Select persona from `personas.py` + rubric from `rubrics.py`
3. **Model Racing** — Send to multiple AI models, select best response
4. **Response Parsing** — Extract grade, feedback, markup JSON
5. **Error Handling** — Retry logic with exponential backoff

### 5.6 `app.py` — Web UI (Panel)

**Responsibility:** Main application entry point using Panel framework.

**Widgets:**
- File upload (PDF, DOCX, PNG, JPG, JPEG)
- Student name text input
- Subject dropdown (Math, English, Science, Programming)
- Grade button
- Progress indicator
- Results preview (image + text)
- PDF download button
- Student history lookup

### 5.7 `personas.py` / `rubrics.py` — Static Configuration

**Responsibility:** Subject-specific AI prompts and scoring criteria.

| Subject | Persona Focus | Rubric Dimensions |
|---------|--------------|-------------------|
| Math | Step-by-step correctness, notation | Accuracy, Method, Presentation |
| English | Grammar, structure, argumentation | Content, Organization, Language, Mechanics |
| Science | Hypothesis, methodology, analysis | Design, Data, Analysis, Conclusion |
| Programming | Code quality, logic, documentation | Functionality, Efficiency, Style, Documentation |

### 5.8 `install_fonts.py` — Setup Utility

**Responsibility:** Download and cache Google Fonts (Caveat, PatrickHand) to `fonts/` directory.

**Behavior:**
- Idempotent — safe to run multiple times
- Downloads from Google Fonts CDN
- Stores locally for offline rendering

---

## 6. Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Teacher   │────►│  File Upload │────►│  Text Extract│────►│  AI Engine  │
│   Action    │     │  (Panel UI)  │     │  (utils.py)  │     │ (engine.py) │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Teacher   │◄────│  PDF Report │◄────│   Markup    │◄────│  AI Response │
│   Receives │     │  (report.py) │     │  (markup.py) │     │  (Parsed)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   History   │
│   Saved     │
│ (storage.py)│
└─────────────┘
```

**Detailed Flow:**

1. **Upload:** Teacher selects file + enters student name + selects subject
2. **Extraction:** `utils.py` routes to PDF/DOCX/OCR extractor based on extension
3. **AI Request:** `engine.py` assembles prompt (persona + rubric + content) and sends to OpenRouter
4. **Model Racing:** Multiple models respond; best response selected
5. **Parsing:** Grade extracted via regex; markup JSON parsed; feedback text isolated
6. **Annotation:** If image file, `markup.py` renders annotations on original image
7. **Report:** `report.py` generates two-page PDF (image + text report)
8. **Persistence:** `storage.py` appends record to `students.json`
9. **Display:** Results shown in Panel UI; PDF available for download

---

## 7. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.9+ | Core implementation |
| **Web Framework** | Panel | 1.9.3 | Interactive web UI |
| **AI API** | OpenRouter | 2.43.0 | Multi-model AI inference |
| **PDF Text Extraction** | PyMuPDF | 1.27.2 | PDF parsing |
| **DOCX Processing** | python-docx | 1.2.0 | Word document parsing |
| **OCR** | pytesseract | 0.3.13 | Image text extraction |
| **Image Processing** | Pillow | 12.2.0 | Annotation rendering |
| **PDF Generation** | ReportLab | 5.0.0 | Report PDF creation |
| **Environment Config** | python-dotenv | 1.2.2 | API key management |
| **System OCR Engine** | Tesseract | 4.1.1+ | Backend for pytesseract |

---

## 8. External Dependencies

### 8.1 OpenRouter API

| Attribute | Value |
|-----------|-------|
| **Type** | REST API |
| **Protocol** | HTTPS |
| **Authentication** | Bearer token (API key) |
| **Payload** | JSON (text + base64 images) |
| **Response** | JSON (text + metadata) |
| **Timeout** | 120 seconds |
| **Retry Policy** | 3 attempts, exponential backoff |

### 8.2 Tesseract OCR

| Attribute | Value |
|-----------|-------|
| **Type** | System binary |
| **Interface** | Python subprocess (via pytesseract) |
| **Languages** | English (eng) |
| **Installation** | OS-level package |

### 8.3 Google Fonts

| Attribute | Value |
|-----------|-------|
| **Type** | CDN download |
| **Fonts** | Caveat, PatrickHand |
| **Caching** | Local `fonts/` directory |
| **Setup** | `install_fonts.py` utility |

---

## 9. Data Stores

### 9.1 `students.json` — Flat-File Database

| Attribute | Value |
|-----------|-------|
| **Type** | JSON flat file |
| **Location** | Project root (`students.json`) |
| **Schema** | Dictionary: `{student_name: {history: [...]}}` |
| **Write Strategy** | Atomic overwrite (read → modify → write) |
| **Concurrency** | File-level locking (implicit, single-user) |
| **Backup** | Manual (no automated backup) |

### 9.2 In-Memory Buffers

| Buffer | Type | Lifecycle |
|--------|------|-----------|
| File upload bytes | `bytes` | Request-scoped |
| Extracted text | `str` | Request-scoped |
| Annotated image | `io.BytesIO` (PNG) | Request-scoped |
| PDF report | `io.BytesIO` | Request-scoped |

---

## 10. Security Architecture

### 10.1 Authentication & Authorization

| Aspect | Implementation |
|--------|----------------|
| API Key Storage | `.env` file (never committed) |
| API Key Access | `os.environ` or `python-dotenv` |
| User Auth | None (single-user local deployment) |
| RBAC | N/A |

### 10.2 Data Protection

| Aspect | Implementation |
|--------|----------------|
| File Upload Validation | Extension whitelist (pdf, docx, png, jpg, jpeg) |
| Input Sanitization | Filename validation in `utils.py` |
| Temp File Handling | In-memory only (no disk persistence) |
| Database Permissions | Owner read/write only (`chmod 600`) |
| Transport Security | HTTPS for all AI API calls |

### 10.3 Threat Model

| Threat | Mitigation |
|--------|------------|
| Malicious file upload | Extension whitelist + in-memory processing |
| API key exposure | `.env` file + `.gitignore` |
| Path traversal | No user-controlled file paths |
| JSON injection | No eval; `json.load()` only |
| OCR DoS | File size limits (future: max 10MB) |

---

## 11. Deployment & Infrastructure

### 11.1 Deployment Options

| Mode | Target | Method |
|------|--------|--------|
| **Local Development** | Developer machine | `python app.py` or `panel serve` |
| **Single-User Desktop** | Teacher's computer | Python virtual environment |
| **Small Team** | Shared server | Docker container (future) |

### 11.2 Runtime Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 1 GB | 5 GB |
| Network | Broadband | Stable broadband |

### 11.3 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter |
| `TESSDATA_PREFIX` | No | Tesseract data directory |
| `MARKLY_DEBUG` | No | Enable debug logging |

---

## 12. Development Environment

### 12.1 Local Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd markly

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Tesseract OCR (system dependency)
# Ubuntu: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: installer from GitHub

# 5. Install fonts
python install_fonts.py

# 6. Configure API key
cp .env.example .env
# Edit .env with your OpenRouter API key

# 7. Run application
panel serve app.py --show
```

### 12.2 Testing Strategy

| Test Type | Framework | Coverage Target |
|-----------|-----------|-----------------|
| Unit Tests | pytest | 80% |
| Integration Tests | pytest + fixtures | 60% |
| E2E Tests | Panel testing utilities | 40% |

### 12.3 Code Quality

| Tool | Purpose | Config |
|------|---------|--------|
| Ruff | Linting + Formatting | `pyproject.toml` |
| mypy | Type checking | `pyproject.toml` |
| pytest | Testing | `pytest.ini` |

---

## 13. Architectural Decisions

### ADR-001: Python + Panel for Web UI

**Status:** Accepted  
**Date:** 2026-06-26

**Context:** Need a rapid web UI for file upload, result display, and PDF download without building a full frontend stack.

**Decision:** Use Panel (HoloViz) — a Python-native framework that generates interactive web apps from Python code.

**Consequences:**
- ✅ No JavaScript/React knowledge required
- ✅ Tight integration with Python data processing
- ✅ Single-file deployment
- ❌ Less customizable than React/Vue
- ❌ Limited theming options

---

### ADR-002: OpenRouter for AI Inference

**Status:** Accepted  
**Date:** 2026-06-26

**Context:** Need access to multiple LLM models (GPT-4, Claude, etc.) without managing multiple API keys and endpoints.

**Decision:** Use OpenRouter as a unified gateway for AI model access.

**Consequences:**
- ✅ Single API key for multiple models
- ✅ Built-in model racing capability
- ✅ Cost optimization via model selection
- ❌ Dependency on third-party service availability
- ❌ Potential latency overhead

---

### ADR-003: JSON Flat-File Database

**Status:** Accepted  
**Date:** 2026-06-26

**Context:** Need simple persistence for student history without operational complexity of a database server.

**Decision:** Use `students.json` as a flat-file database with atomic writes.

**Consequences:**
- ✅ Zero setup (no DB server)
- ✅ Human-readable format
- ✅ Easy backup/restore
- ❌ No concurrent write support
- ❌ Performance degrades at >10K records
- ❌ No query capabilities

---

### ADR-004: Pillow for Visual Annotations

**Status:** Accepted  
**Date:** 2026-06-26

**Context:** Need to render teacher-style handwriting annotations on assignment images.

**Decision:** Use Pillow (PIL) with custom jitter algorithms to simulate hand-drawn marks.

**Consequences:**
- ✅ Full control over rendering
- ✅ No external image editing dependencies
- ✅ Deterministic output with seeded randomness
- ❌ Complex shapes require manual implementation
- ❌ Performance limited by Python GIL

---

### ADR-005: ReportLab for PDF Generation

**Status:** Accepted  
**Date:** 2026-06-26

**Context:** Need to generate two-page PDF reports with mixed content (images + text + tables).

**Decision:** Use ReportLab for programmatic PDF generation.

**Consequences:**
- ✅ Precise layout control
- ✅ No external dependencies (pure Python)
- ✅ Supports complex table structures
- ❌ Steeper learning curve than HTML-to-PDF
- ❌ Manual styling required

---

## 14. Future Considerations

### 14.1 Technical Debt

| Item | Impact | Priority |
|------|--------|----------|
| JSON database scalability | Medium | Medium |
| No automated testing | High | High |
| Single-threaded processing | Medium | Medium |
| Hardcoded font paths | Low | Low |

### 14.2 Planned Enhancements

| Feature | Target Version | Description |
|---------|---------------|-------------|
| LMS Integration | v2.0 | Canvas/Blackboard/Moodle API |
| Multi-language Support | v2.0 | Non-English assignments |
| Batch Processing | v1.5 | Multiple assignments at once |
| Cloud Storage | v1.5 | S3/Azure Blob for file persistence |
| User Authentication | v2.0 | Login and role-based access |
| Docker Deployment | v1.5 | Containerized deployment |
| Async Processing | v1.5 | Background job queue (Celery/RQ) |

### 14.3 Migration Paths

| From | To | Trigger |
|------|-----|---------|
| JSON flat-file | SQLite/PostgreSQL | >1000 students or multi-user |
| Single-process | Async workers | Batch processing requirement |
| Local fonts | CDN with fallback | Dynamic font loading |
| Panel UI | FastAPI + React | Enterprise deployment |

---

## 15. Glossary

| Term | Definition |
|------|------------|
| **Markly** | The AI-powered assignment grading system |
| **Panel** | Python web framework for interactive dashboards |
| **OpenRouter** | Unified API gateway for multiple LLM providers |
| **PyMuPDF** | Python bindings for MuPDF (PDF rendering engine) |
| **Tesseract** | Open-source OCR engine maintained by Google |
| **Pillow** | Python Imaging Library (fork of PIL) |
| **ReportLab** | Python library for PDF document generation |
| **Markup JSON** | Structured annotation instructions for `markup.py` |
| **Model Racing** | Sending same prompt to multiple AI models and comparing responses |
| **Jitter** | Random coordinate offset for hand-drawn simulation |
| **Persona** | Subject-specific AI prompt template |
| **Rubric** | Scoring criteria with point allocations |
| **ADR** | Architecture Decision Record |

---

## Appendix: File Structure

```
markly/
├── app.py                  # Main Panel UI application
├── engine.py               # AI grading pipeline (OpenRouter)
├── utils.py                # File ingestion and text extraction
├── markup.py               # Visual annotation engine
├── report.py               # PDF report generation
├── storage.py              # JSON persistence layer
├── personas.py             # AI prompt templates per subject
├── rubrics.py              # Scoring criteria per subject
├── install_fonts.py        # Font setup utility
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (gitignored)
├── .env.example            # Environment template
├── students.json           # Flat-file database (gitignored)
├── fonts/                  # Local font cache
│   ├── Caveat-Regular.ttf
│   └── PatrickHand-Regular.ttf
├── README.md               # Project overview
├── ARCHITECTURE.md         # This document
└── docs/                   # Additional documentation
    └── ...
```

---

**Document Owner:** Sean Wong
**Review Cycle:** Upon major architectural change  
**Next Review:** 2026-09-26

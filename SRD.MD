# Software Requirements Specification (SRS)

## For Markly: AI-Powered Assignment Grading & Feedback System

**Version 1.0**

**Prepared by:** AI Systems Architect

**Organization:** Markly Development Team

**Date Created:** 2026-06-26

---

## Table of Contents

1. Introduction
2. Overall Description
3. System Features
4. External Interface Requirements
5. System Features / Functional Requirements
6. Non-Functional Requirements
7. Other Requirements
8. Appendices

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the complete set of functional and non-functional requirements for **Markly**, an AI-powered assignment grading and feedback system. Markly automates the evaluation of student assignments across multiple subjects (Math, English, Science, Programming) by ingesting various file formats, applying AI-driven assessment via the OpenRouter API, generating teacher-style visual annotations, and producing structured PDF reports.

### 1.2 Document Conventions

- **Requirement IDs:** All requirements are uniquely identified using the format `REQ-{Module}-{Number}` for functional requirements and `NF-{Category}-{Number}` for non-functional requirements.
- **Priority Levels:** High (H), Medium (M), Low (L) — indicated after each requirement.
- **Shall/Should/May:** "Shall" denotes mandatory requirements; "Should" denotes recommended; "May" denotes optional.
- **Traceability:** Each requirement is cross-referenced to its source module and test case.

### 1.3 Intended Audience and Reading Suggestions

| Audience | Recommended Sections | Purpose |
|----------|---------------------|---------|
| Developers | Sections 2, 3, 4, 5 | Implementation guidance |
| QA/Testers | Sections 5, 6, 7 | Test planning and validation |
| Project Managers | Sections 1, 2, 6 | Scope and resource planning |
| DevOps/SRE | Sections 4, 6.1, 6.2 | Deployment and infrastructure |
| UI/UX Designers | Sections 4.1, 5.2 | Interface design |

### 1.4 Product Scope

Markly is a web-based application that enables teachers to upload student assignments (PDF, DOCX, images), automatically grades them using AI models via OpenRouter, generates visual annotations mimicking handwritten teacher feedback, and produces downloadable PDF reports. The system supports multi-subject grading with subject-specific rubrics and maintains a persistent history of student records.

**In Scope:**
- File ingestion (PDF, DOCX, PNG, JPG, JPEG)
- AI-powered grading and feedback generation
- Visual annotation rendering on assignment images
- PDF report generation (two-page format)
- Student history tracking via JSON flat-file database
- Panel-based web UI for teacher interaction

**Out of Scope:**
- Real-time collaborative editing
- Student-facing portal
- LMS integration (future version)
- Multi-language support beyond English (future version)

### 1.5 References

| Reference | Description |
|-----------|-------------|
| [1] | IEEE Std 830-1998, IEEE Recommended Practice for Software Requirements Specifications |
| [2] | ISO/IEC/IEEE 29148:2018, Systems and software engineering — Life cycle processes — Requirements engineering |
| [3] | OpenRouter API Documentation (https://openrouter.ai/docs) |
| [4] | PyMuPDF Documentation (v1.27.2) |
| [5] | Panel Documentation (v1.9.3) |
| [6] | ReportLab Documentation (v5.0.0) |

### 1.6 Overview

This document is organized into six main sections. Section 2 provides the overall system context. Section 3 outlines system features at a high level. Section 4 details external interfaces. Section 5 contains the detailed functional requirements organized by module. Section 6 defines non-functional requirements. Section 7 covers other requirements, and Section 8 contains appendices.

---

## 2. Overall Description

### 2.1 Product Perspective

Markly is a standalone web application designed for individual teachers or small educational institutions. It operates as a self-contained system with external dependencies on AI APIs (OpenRouter) and system-level libraries (Tesseract OCR). The system does not replace existing Learning Management Systems (LMS) but provides a specialized tool for automated assignment grading.

**System Context Diagram:**

```
[Teacher/User] ←→ [Markly Web UI (Panel)] ←→ [AI Engine (OpenRouter)]
                           ↓
                    [File Processing] ←→ [Visual Annotation]
                           ↓
                    [PDF Report Generation]
                           ↓
                    [JSON Storage (students.json)]
```

### 2.2 Product Features

| Feature ID | Feature Name | Description |
|------------|-------------|-------------|
| F-01 | File Ingestion | Extract text from PDF, DOCX, and image files |
| F-02 | AI Grading Pipeline | Send extracted content to OpenRouter for assessment |
| F-03 | Subject Detection | Automatically identify subject from assignment content |
| F-04 | Model Racing | Compare multiple AI models and select best response |
| F-05 | Visual Annotation | Render teacher-style markup on assignment images |
| F-06 | PDF Report Generation | Create two-page PDF with annotated image and feedback |
| F-07 | History Tracking | Persist student grades and feedback in JSON database |
| F-08 | Web UI | Panel-based interface for upload, review, and download |

### 2.3 User Classes and Characteristics

| User Class | Description | Technical Skill | Usage Frequency |
|------------|-------------|-----------------|-----------------|
| Primary Teacher | Main user who uploads, reviews, and downloads graded assignments | Low to Medium | Daily |
| Administrator | Manages system configuration, API keys, font installation | Medium to High | Weekly |
| Student | Receives annotated assignments and reports (passive) | N/A | Per assignment |

### 2.4 Operating Environment

| Component | Requirement |
|-----------|-------------|
| Hardware | x86_64 or ARM64 processor, minimum 4GB RAM |
| OS | Linux (Ubuntu 20.04+), macOS 12+, Windows 10/11 |
| Python | 3.9 or higher |
| Tesseract OCR | System-installed (v4.1.1 or higher) |
| Browser | Chrome 100+, Firefox 100+, Safari 15+ |

### 2.5 Design and Implementation Constraints

- **CON-01:** The system must use Python as the primary implementation language.
- **CON-02:** The web UI must be built using the Panel framework (v1.9.3).
- **CON-03:** AI inference must be routed through the OpenRouter API.
- **CON-04:** All persistence must use a JSON flat-file database (`students.json`); no relational database is permitted.
- **CON-05:** Visual annotations must use Pillow (PIL) for image manipulation.
- **CON-06:** PDF generation must use ReportLab (v5.0.0).
- **CON-07:** The system must support offline font rendering; Google Fonts must be locally cached.

### 2.6 User Documentation

- User Manual: Step-by-step guide for uploading and grading assignments
- API Key Setup Guide: Instructions for configuring OpenRouter API credentials
- Font Installation Guide: Instructions for running `install_fonts.py`
- Troubleshooting Guide: Common errors and resolutions

### 2.7 Assumptions and Dependencies

| ID | Assumption | Risk if Invalid |
|----|-----------|-----------------|
| ASM-01 | OpenRouter API is available and responsive | System cannot perform grading |
| ASM-02 | Tesseract OCR is installed on the host system | Image text extraction fails |
| ASM-03 | System has internet connectivity for AI API calls | AI grading pipeline fails |
| ASM-04 | Sufficient disk space for font caching and PDF generation | Report generation fails |
| DEP-01 | PyMuPDF v1.27.2 for PDF text extraction | PDF processing errors |
| DEP-02 | python-docx v1.2.0 for DOCX processing | DOCX extraction fails |
| DEP-03 | Pillow v12.2.0 for image manipulation | Annotation rendering fails |
| DEP-04 | pytesseract v0.3.13 for OCR | Image text extraction fails |

---

## 3. System Features (High-Level)

### 3.1 File Ingestion and Processing
Markly shall accept uploaded files in PDF, DOCX, PNG, JPG, and JPEG formats and extract textual content for AI processing.

### 3.2 AI Grading Engine
Markly shall send extracted assignment content to the OpenRouter API, support model racing across multiple AI models, and apply subject-specific rubrics for grading.

### 3.3 Visual Annotation
Markly shall render teacher-style annotations (ticks, crosses, circles, wavy underlines, margin notes, score stamps, correction boxes, summary blocks) directly onto assignment images.

### 3.4 PDF Report Generation
Markly shall generate a two-page PDF report containing the annotated assignment image and a structured text feedback report with metadata.

### 3.5 History Tracking
Markly shall persist student grading records in a JSON flat-file database and support retrieval of historical records.

### 3.6 Web User Interface
Markly shall provide a Panel-based web interface for file upload, grading initiation, result review, and report download.

---

## 4. External Interface Requirements

### 4.1 User Interfaces

**UI-01:** The system shall provide a web-based interface accessible via standard browsers.

**UI-02:** The interface shall include:
- File upload widget (drag-and-drop or file picker)
- Student name input field
- Subject selection dropdown (Math, English, Science, Programming)
- "Grade Assignment" action button
- Results preview panel (annotated image + feedback text)
- PDF download button
- Student history lookup panel

**UI-03:** The interface shall display real-time processing status during AI grading.

**UI-04:** Error messages shall be displayed in a user-friendly format with suggested remediation steps.

### 4.2 Hardware Interfaces

**HW-01:** The system requires a standard x86_64 or ARM64 server with minimum 4GB RAM.

**HW-02:** No specialized hardware interfaces are required; standard file I/O operations suffice.

### 4.3 Software Interfaces

| Interface | Component | Data Format | Protocol |
|-----------|-----------|-------------|----------|
| SI-01 | OpenRouter API | JSON (REST) | HTTPS |
| SI-02 | Tesseract OCR | Text | System subprocess |
| SI-03 | PyMuPDF | Text/Bytes | Python API |
| SI-04 | python-docx | Text | Python API |
| SI-05 | Pillow (PIL) | Image bytes | Python API |
| SI-06 | ReportLab | PDF bytes | Python API |
| SI-07 | Panel | HTML/JS | WebSocket/HTTP |

### 4.4 Communications Interfaces

**COM-01:** All AI API communications shall use HTTPS with TLS 1.2 or higher.

**COM-02:** API requests to OpenRouter shall include authentication headers with the user's API key.

**COM-03:** The system shall implement request timeout handling (default: 120 seconds) for AI API calls.

---

## 5. System Features / Functional Requirements

### 5.1 Module: utils.py — File Ingestion and Processing

#### 5.1.1 Description and Priority
Handles text extraction from various file formats and basic data processing. **Priority: High**

#### 5.1.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| User uploads a PDF file | System extracts text page by page |
| User uploads a DOCX file | System extracts all paragraph text |
| User uploads an image file | System performs OCR and returns extracted text |
| Unsupported file uploaded | System raises ValueError with clear message |

#### 5.1.3 Functional Requirements

**REQ-UTIL-01:** The system shall extract text from PDF files using PyMuPDF, returning concatenated text from all pages.

**REQ-UTIL-02:** The system shall extract text from DOCX files using python-docx, returning concatenated paragraph text.

**REQ-UTIL-03:** The system shall extract text from image files (PNG, JPG, JPEG) using Tesseract OCR via pytesseract.

**REQ-UTIL-04:** The system shall provide a unified `extract_text_from_file(file_bytes, filename)` function that routes to the appropriate extractor based on file extension.

**REQ-UTIL-05:** The system shall reject unsupported file types with a `ValueError` containing the filename.

**REQ-UTIL-06:** The system shall encode image bytes to base64 format for AI API consumption via `image_to_base64()`.

**REQ-UTIL-07:** The system shall extract numerical grades from AI-generated text using regex patterns matching:
- `X/10` format
- `Grade: X` format (A-F with optional +/-)
- `X/100`, `X/20`, `X/50` formats

**REQ-UTIL-08:** The `extract_grade()` function shall return "N/A" if no grade pattern is found.

---

### 5.2 Module: markup.py — Teacher-Style Image Annotations

#### 5.2.1 Description and Priority
Renders handwriting-style annotations on student assignment images using Pillow. **Priority: High**

#### 5.2.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| AI grading completes with markup JSON | System renders annotations on original image |
| Markup specifies a tick | System draws a jittered checkmark |
| Markup specifies a cross | System draws a jittered X mark |
| Markup specifies a circle | System draws a wobbly ellipse |
| Markup specifies a correction | System draws a rounded rectangle with wavy underline |

#### 5.2.3 Functional Requirements

**REQ-MARK-01:** The system shall use a deterministic random seed (seed=42) for semi-reproducible jitter in hand-drawn annotations.

**REQ-MARK-02:** The system shall implement a font cache (`_FONT_CACHE`) to improve performance by avoiding repeated font loading.

**REQ-MARK-03:** The system shall apply small random offsets (`_jitter()`, ±2.5px default) to simulate human handwriting variability.

**REQ-MARK-04:** The system shall draw jittered lines by segmenting straight lines into 6 segments with per-point random offsets.

**REQ-MARK-05:** The system shall render wavy underlines using sinusoidal curves with configurable amplitude (default 5px) and wavelength (default 14px).

**REQ-MARK-06:** The system shall render wobbly ellipses by applying radius wobble (0.93-1.07x) and angle wobble (±0.04 rad) to circle points.

**REQ-MARK-07:** The system shall draw rounded rectangles using arc segments for corners and straight lines for edges.

**REQ-MARK-08:** The system shall render speech bubbles with text wrapping based on image width (max_chars = 20% of image width).

**REQ-MARK-09:** The system shall draw tick marks (checkmarks) with three connected jittered line segments.

**REQ-MARK-10:** The system shall draw cross marks (X) with two diagonal jittered lines.

**REQ-MARK-11:** The system shall render score stamps with large numerator and small denominator text in circular format.

**REQ-MARK-12:** The system shall draw correction boxes with semi-transparent fill (alpha=35), rounded outline, and wavy underline.

**REQ-MARK-13:** The system shall render margin notes on the left or right side with wrapped text and background boxes.

**REQ-MARK-14:** The system shall render summary blocks as semi-transparent yellow feedback blocks at the bottom of the image.

**REQ-MARK-15:** The main entry point `draw_teacher_markup(image_bytes, markup_json)` shall return an `io.BytesIO` buffer containing the annotated PNG image.

---

### 5.3 Module: report.py — PDF Report Generation

#### 5.3.1 Description and Priority
Generates structured PDF reports using ReportLab. **Priority: High**

#### 5.3.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Grading completes with image and feedback | System generates two-page PDF |
| Assignment has no image (text-only) | System generates text-focused PDF |

#### 5.3.3 Functional Requirements

**REQ-REP-01:** The system shall generate a two-page PDF report (`create_marked_pdf()`) with:
- Page 1: Annotated assignment image (scaled to fit A4)
- Page 2: Structured text report with metadata table

**REQ-REP-02:** The metadata table shall include Student name, Subject, and Filename fields.

**REQ-REP-03:** The text report page shall include overall feedback, grade, and detailed corrections.

**REQ-REP-04:** The system shall provide a text-only PDF report (`create_pdf_report()`) for non-image assignments.

**REQ-REP-05:** All PDFs shall use A4 page size (210mm × 297mm).

**REQ-REP-06:** The system shall use ReportLab paragraph styles for consistent text formatting.

---

### 5.4 Module: storage.py — Persistence

#### 5.4.1 Description and Priority
Handles reading and writing to `students.json` for history tracking. **Priority: Medium**

#### 5.4.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Grading completes | System appends record to student's history |
| User requests student history | System retrieves all previous records |

#### 5.4.3 Functional Requirements

**REQ-STOR-01:** The system shall use a JSON flat-file database (`students.json`) for all persistent storage.

**REQ-STOR-02:** The `load_db()` function shall return an empty dictionary if the file does not exist or is corrupted.

**REQ-STOR-03:** The `save_db()` function shall write the database state with 2-space indentation.

**REQ-STOR-04:** The `add_record()` function shall create a new student entry with empty history if the student does not exist.

**REQ-STOR-05:** Each history entry shall include: timestamp, subject, grade, and feedback.

**REQ-STOR-06:** The `get_student_history()` function shall return a formatted string of all records or "No previous records." if none exist.

---

### 5.5 Module: engine.py — AI Grading Pipeline (Architectural)

#### 5.5.1 Description and Priority
Handles OpenRouter AI pipeline, model racing, and subject detection. **Priority: High**

#### 5.5.2 Functional Requirements

**REQ-ENG-01:** The system shall send extracted assignment text and images (base64) to the OpenRouter API.

**REQ-ENG-02:** The system shall support model racing across multiple AI models and select the best response based on confidence or quality metrics.

**REQ-ENG-03:** The system shall automatically detect the subject from assignment content when not explicitly specified.

**REQ-ENG-04:** The system shall apply subject-specific prompts from `personas.py` and scoring rubrics from `rubrics.py`.

**REQ-ENG-05:** The system shall parse AI responses to extract grades, feedback text, and markup JSON.

**REQ-ENG-06:** The system shall handle API errors gracefully with retry logic and user-friendly error messages.

---

### 5.6 Module: app.py — Web UI (Architectural)

#### 5.6.1 Description and Priority
Main Panel application wiring widgets and callbacks. **Priority: High**

#### 5.6.2 Functional Requirements

**REQ-APP-01:** The system shall provide a file upload widget supporting PDF, DOCX, PNG, JPG, and JPEG.

**REQ-APP-02:** The system shall provide input fields for student name and subject selection.

**REQ-APP-03:** The system shall display a "Grade" button that initiates the full pipeline.

**REQ-APP-04:** The system shall show a progress indicator during processing.

**REQ-APP-05:** The system shall display the annotated image preview upon completion.

**REQ-APP-06:** The system shall display the extracted feedback text in a readable format.

**REQ-APP-07:** The system shall provide a download button for the generated PDF report.

**REQ-APP-08:** The system shall allow lookup of student history by name.

---

### 5.7 Module: personas.py / rubrics.py (Architectural)

#### 5.7.1 Functional Requirements

**REQ-PER-01:** The system shall contain static prompt templates for Math, English, Science, and Programming subjects.

**REQ-PER-02:** Each persona shall define the AI's grading personality, tone, and evaluation criteria.

**REQ-RUB-01:** The system shall contain subject-specific scoring rubrics with point allocations and criteria descriptions.

**REQ-RUB-02:** Rubrics shall be versioned and referenced by the engine module during grading.

---

### 5.8 Module: install_fonts.py (Utility)

#### 5.8.1 Functional Requirements

**REQ-FONT-01:** The system shall provide a utility script to download and cache Google Fonts (Caveat, PatrickHand) into a local `fonts/` directory.

**REQ-FONT-02:** The script shall be idempotent — running multiple times shall not create duplicates.

---

## 6. Non-Functional Requirements

### 6.1 Performance Requirements

**NF-PERF-01:** The system shall process a single-page PDF text extraction in under 2 seconds.

**NF-PERF-02:** The system shall complete a full AI grading pipeline (upload → AI response → annotation → PDF) in under 60 seconds for assignments under 5 pages.

**NF-PERF-03:** The system shall support concurrent processing of at least 2 assignments without degradation.

**NF-PERF-04:** The font cache shall reduce font loading time by at least 80% on subsequent operations.

**NF-PERF-05:** The JSON database shall handle up to 10,000 student records without significant performance degradation.

### 6.2 Security Requirements

**NF-SEC-01:** The system shall store the OpenRouter API key in environment variables (via `.env` file) and never hardcode it in source.

**NF-SEC-02:** The system shall validate all uploaded file types before processing to prevent malicious file execution.

**NF-SEC-03:** The system shall sanitize all user inputs (student names, filenames) to prevent injection attacks.

**NF-SEC-04:** The system shall not persist uploaded files permanently; temporary files shall be deleted after processing.

**NF-SEC-05:** The `students.json` file shall have restrictive file permissions (read/write for owner only).

### 6.3 Reliability Requirements

**NF-REL-01:** The system shall handle corrupted PDF/DOCX files gracefully, returning a clear error message without crashing.

**NF-REL-02:** The system shall implement retry logic (3 attempts, exponential backoff) for transient OpenRouter API failures.

**NF-REL-03:** The system shall maintain data integrity in `students.json` using atomic write operations.

**NF-REL-04:** The system shall log all errors to a rotating log file for debugging purposes.

### 6.4 Usability Requirements

**NF-USE-01:** The web interface shall be usable by teachers with no programming experience.

**NF-USE-02:** All error messages shall be actionable and explain how to resolve the issue.

**NF-USE-03:** The PDF report layout shall be readable on standard A4 printouts.

**NF-USE-04:** Visual annotations shall be clearly distinguishable from original assignment content.

### 6.5 Maintainability Requirements

**NF-MAINT-01:** The system shall follow PEP 8 style guidelines for Python code.

**NF-MAINT-02:** All functions shall include docstrings describing parameters, return values, and exceptions.

**NF-MAINT-03:** The system shall use semantic versioning for releases.

**NF-MAINT-04:** Configuration variables (API endpoints, timeouts, file paths) shall be centralized in a configuration module or `.env` file.

### 6.6 Portability Requirements

**NF-PORT-01:** The system shall run on Linux, macOS, and Windows with Python 3.9+.

**NF-PORT-02:** All dependencies shall be specified in `requirements.txt` with pinned versions.

**NF-PORT-03:** The system shall not require root/administrator privileges for standard operation.

---

## 7. Other Requirements

### 7.1 Database Requirements

**DB-01:** The system shall use a single JSON file (`students.json`) as the database.

**DB-02:** The database schema shall be a dictionary with student names as keys and history arrays as values.

**DB-03:** Each history entry shall be a dictionary with keys: `timestamp`, `subject`, `grade`, `feedback`.

### 7.2 Legal and Regulatory Requirements

**LEGAL-01:** The system shall comply with educational data privacy standards (FERPA considerations for US institutions).

**LEGAL-02:** The system shall not store personally identifiable information beyond student names and assignment metadata.

### 7.3 Internationalization Requirements

**I18N-01:** The system shall use UTF-8 encoding for all text processing and file I/O.

**I18N-02:** The system shall support Unicode characters in student names and assignment content.

### 7.4 Risk Management

| Risk ID | Risk Description | Mitigation |
|---------|-----------------|------------|
| RISK-01 | OpenRouter API rate limiting or downtime | Implement caching and offline queue |
| RISK-02 | Tesseract OCR accuracy on poor-quality images | Pre-process images (contrast, deskew) |
| RISK-03 | Large file uploads causing memory issues | Implement file size limits (max 10MB) |
| RISK-04 | JSON database corruption | Implement backup and atomic writes |
| RISK-05 | AI hallucination in grading | Multi-model consensus and human review |

---

## 8. Appendices

### 8.1 Glossary

| Term | Definition |
|------|------------|
| Markup JSON | Structured JSON describing annotations to render on an image |
| Model Racing | Sending the same prompt to multiple AI models and comparing responses |
| Jitter | Random offset applied to coordinates to simulate hand-drawn appearance |
| OpenRouter | Third-party API service providing access to multiple AI models |
| Panel | Python library for building interactive web apps and dashboards |

### 8.2 Traceability Matrix

| Requirement ID | Module | Test Case | Priority |
|----------------|--------|-----------|----------|
| REQ-UTIL-01 | utils.py | TC-UTIL-01 | High |
| REQ-UTIL-02 | utils.py | TC-UTIL-02 | High |
| REQ-UTIL-03 | utils.py | TC-UTIL-03 | High |
| REQ-UTIL-04 | utils.py | TC-UTIL-04 | High |
| REQ-UTIL-05 | utils.py | TC-UTIL-05 | High |
| REQ-UTIL-06 | utils.py | TC-UTIL-06 | Medium |
| REQ-UTIL-07 | utils.py | TC-UTIL-07 | High |
| REQ-UTIL-08 | utils.py | TC-UTIL-08 | Medium |
| REQ-MARK-01 | markup.py | TC-MARK-01 | High |
| REQ-MARK-02 | markup.py | TC-MARK-02 | Medium |
| REQ-MARK-03 | markup.py | TC-MARK-03 | High |
| REQ-MARK-04 | markup.py | TC-MARK-04 | High |
| REQ-MARK-05 | markup.py | TC-MARK-05 | High |
| REQ-MARK-06 | markup.py | TC-MARK-06 | High |
| REQ-MARK-07 | markup.py | TC-MARK-07 | High |
| REQ-MARK-08 | markup.py | TC-MARK-08 | Medium |
| REQ-MARK-09 | markup.py | TC-MARK-09 | High |
| REQ-MARK-10 | markup.py | TC-MARK-10 | High |
| REQ-MARK-11 | markup.py | TC-MARK-11 | Medium |
| REQ-MARK-12 | markup.py | TC-MARK-12 | High |
| REQ-MARK-13 | markup.py | TC-MARK-13 | Medium |
| REQ-MARK-14 | markup.py | TC-MARK-14 | Medium |
| REQ-MARK-15 | markup.py | TC-MARK-15 | High |
| REQ-REP-01 | report.py | TC-REP-01 | High |
| REQ-REP-02 | report.py | TC-REP-02 | High |
| REQ-REP-03 | report.py | TC-REP-03 | High |
| REQ-REP-04 | report.py | TC-REP-04 | Medium |
| REQ-REP-05 | report.py | TC-REP-05 | High |
| REQ-REP-06 | report.py | TC-REP-06 | Medium |
| REQ-STOR-01 | storage.py | TC-STOR-01 | Medium |
| REQ-STOR-02 | storage.py | TC-STOR-02 | Medium |
| REQ-STOR-03 | storage.py | TC-STOR-03 | Medium |
| REQ-STOR-04 | storage.py | TC-STOR-04 | Medium |
| REQ-STOR-05 | storage.py | TC-STOR-05 | Medium |
| REQ-STOR-06 | storage.py | TC-STOR-06 | Medium |
| REQ-ENG-01 | engine.py | TC-ENG-01 | High |
| REQ-ENG-02 | engine.py | TC-ENG-02 | High |
| REQ-ENG-03 | engine.py | TC-ENG-03 | High |
| REQ-ENG-04 | engine.py | TC-ENG-04 | High |
| REQ-ENG-05 | engine.py | TC-ENG-05 | High |
| REQ-ENG-06 | engine.py | TC-ENG-06 | High |
| REQ-APP-01 | app.py | TC-APP-01 | High |
| REQ-APP-02 | app.py | TC-APP-02 | High |
| REQ-APP-03 | app.py | TC-APP-03 | High |
| REQ-APP-04 | app.py | TC-APP-04 | Medium |
| REQ-APP-05 | app.py | TC-APP-05 | High |
| REQ-APP-06 | app.py | TC-APP-06 | High |
| REQ-APP-07 | app.py | TC-APP-07 | High |
| REQ-APP-08 | app.py | TC-APP-08 | Medium |

### 8.3 To Be Determined (TBD) List

| ID | Item | Description | Target Date |
|----|------|-------------|-------------|
| TBD-01 | LMS Integration | API specifications for Canvas/Blackboard/Moodle | v2.0 |
| TBD-02 | Multi-language Support | i18n framework for non-English assignments | v2.0 |
| TBD-03 | Batch Processing | Upload and grade multiple assignments simultaneously | v1.5 |
| TBD-04 | Cloud Storage | S3/Azure Blob integration for file persistence | v1.5 |
| TBD-05 | Authentication | User login and role-based access control | v2.0 |

---

## Revision History

| Version | Date | Author | Reason for Changes |
|---------|------|--------|-------------------|
| 0.1 | 2026-06-26 | AI Systems Architect | Initial draft based on source code analysis |
| 1.0 | 2026-06-26 | AI Systems Architect | Finalized SRD with complete requirements |

# 🎓 Markly — AI-Powered Assignment Grading Assistant

## 🚀 Live Demo

Try Markly online:

**🌐 Demo:** https://huggingface.co/spaces/seanwhs/Markly

No installation required. Upload an assignment and experience the complete grading workflow directly from your browser.

---

# Why I Built Markly

Markly is my second serious attempt at building an AI-powered application.

My goal wasn't simply to call a Large Language Model and generate text. I wanted to explore how real AI systems are engineered end-to-end by combining document processing, OCR, classification, grading, visual annotation, PDF generation, memory, and persistence into a complete educational workflow.

Teachers spend a significant amount of time reviewing assignments, writing feedback, and generating reports. Markly is my attempt to reduce that workload by acting as an AI teaching assistant that can:

* Read assignments
* Detect subjects automatically
* Apply grading rubrics
* Generate structured feedback
* Create teacher-style annotations
* Track student progress over time
* Produce professional reports

The project also serves as a practical exploration of AI engineering concepts including:

* Vision models
* OCR pipelines
* Prompt orchestration
* Concurrent model execution
* Structured AI outputs
* Workflow automation
* Human-in-the-loop assessment systems

---

# Features

## 🧠 Automatic Subject Detection

Teachers no longer need to manually classify assignments.

Markly analyzes uploaded content and predicts the most appropriate subject:

* Mathematics
* English
* Science
* Programming

The detected subject automatically determines:

* Grading rubric
* Teacher persona
* Evaluation criteria
* Feedback style

---

## 📋 Rubric-Based Evaluation

Every subject is evaluated using a dedicated rubric to promote consistency and transparency.

Examples include:

### Mathematics

* Calculation accuracy
* Method correctness
* Final answer validation

### English

* Grammar and syntax
* Writing clarity
* Argument strength

### Science

* Scientific reasoning
* Evidence usage
* Conceptual understanding

### Programming

* Correctness
* Code quality
* Maintainability
* Software engineering practices

---

## 👨‍🏫 AI Teacher Personas

Markly uses specialized grading personas that simulate subject-matter educators.

Examples include:

* Mathematics teacher
* English language teacher
* Science educator
* Software engineering instructor

Each persona generates feedback appropriate to the discipline being assessed.

---

## ✍️ Teacher-Style Assignment Markup

One of Markly's most distinctive features is its ability to generate visual annotations directly on student submissions.

For image-based assignments, Markly can create:

* ✓ Correct-answer ticks
* ✗ Incorrect-answer crosses
* Circled marks
* Teacher comments
* Margin notes
* Correction suggestions
* Encouragement remarks
* Summary feedback

The annotations are rendered using Pillow and handwriting-inspired fonts to mimic real teacher grading.

This transforms AI-generated feedback into something students immediately recognize and understand.

---

## 📄 Professional PDF Reports

Markly automatically generates downloadable grading reports containing:

* Student information
* Subject classification
* Final grade
* Strengths
* Areas for improvement
* Teacher comments
* AI evaluation summary
* Annotated assignment pages

Reports are designed to be shareable with students, parents, and administrators.

---

## 🧠 Student Memory & Progress Tracking

Unlike traditional grading tools that evaluate assignments in isolation, Markly maintains a history of student performance.

This enables:

* Progress tracking
* Trend identification
* Historical feedback review
* Longitudinal assessment

Future versions will leverage this data to generate personalized learning insights.

---

## ⚡ Concurrent AI Processing

Markly uses a model-racing strategy to improve responsiveness and reliability.

Multiple AI models can be queried simultaneously.

The first successful result is returned while slower requests are discarded.

Benefits include:

* Faster responses
* Increased availability
* Better fault tolerance
* Reduced dependency on a single model

---

# Architecture Overview

Current implementation follows a lightweight monolithic architecture while validating product-market fit and user experience.

```text
Teacher Uploads Assignment
            │
            ▼
Document Processing
            │
            ▼
OCR / Content Extraction
            │
            ▼
Subject Detection
            │
            ▼
Rubric Selection
            │
            ▼
AI Evaluation
            │
            ├──────────────► Student Memory
            │
            ├──────────────► PDF Report
            │
            ▼
Annotation Generation
            │
            ▼
Marked Assignment Output
```

---

# Project Structure

```text
markly/
│
├── app.py
├── engine.py
├── markup.py
├── report.py
├── storage.py
├── utils.py
├── personas.py
├── rubrics.py
├── install_fonts.py
│
├── fonts/
│   ├── Caveat-Regular.ttf
│   ├── Caveat-Bold.ttf
│   └── PatrickHand-Regular.ttf
│
├── students.json
├── requirements.txt
└── README.md
```

## Module Responsibilities

| File             | Responsibility                                              |
| ---------------- | ----------------------------------------------------------- |
| app.py           | UI workflow orchestration                                   |
| engine.py        | AI integration, subject detection, grading, vision analysis |
| markup.py        | Teacher-style annotation rendering                          |
| report.py        | PDF report generation                                       |
| storage.py       | Student history persistence                                 |
| utils.py         | OCR and document extraction                                 |
| personas.py      | Teacher personas                                            |
| rubrics.py       | Grading rubrics                                             |
| install_fonts.py | Font installation                                           |

---

# Technology Stack

| Layer             | Technology          |
| ----------------- | ------------------- |
| Frontend          | Panel               |
| Hosting           | Hugging Face Spaces |
| AI Gateway        | OpenRouter          |
| LLM Client        | AsyncOpenAI         |
| OCR               | Tesseract           |
| PDF Parsing       | PyMuPDF             |
| DOCX Parsing      | python-docx         |
| Image Processing  | Pillow              |
| Report Generation | ReportLab           |
| Concurrency       | asyncio             |
| Persistence       | JSON                |

---

# Supported Formats

Markly currently supports:

* PDF
* DOCX
* PNG
* JPG
* JPEG

For image-based submissions, OCR and visual analysis are automatically applied.

---

# Local Installation

## Clone Repository

```bash
git clone <repository-url>
cd markly
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

## Install Fonts

```bash
python install_fonts.py
```

## Launch Application

```bash
panel serve app.py
```

---

# What I Learned

Markly reinforced an important lesson:

Building AI systems is not just prompt engineering.

Real-world AI applications require solving problems across multiple domains:

* Document ingestion
* OCR reliability
* AI orchestration
* Structured outputs
* Annotation rendering
* Report generation
* State management
* Persistence
* Fault tolerance
* User experience

The AI model is only one component of the overall system.

The engineering around the model is often the harder problem.

---

# Future Roadmap

Planned enhancements include:

## Product Features

* Multi-page annotation support
* Batch assignment processing
* Teacher profile customization
* Classroom analytics dashboard
* RAG-powered feedback generation
* Cloud storage integration
* Student learning recommendations
* Curriculum-aware grading

## AI Enhancements

* Better handwriting recognition
* Rubric grounding
* Citation-aware feedback
* Multi-model consensus grading
* Hallucination reduction workflows

---

# Disclaimer

Markly is designed to assist educators, not replace them.

AI-generated grades, comments, and recommendations should always be reviewed by a qualified teacher before being shared with students.

Final assessment responsibility remains with the educator.

import panel as pn
import json
import asyncio
import logging
import html
from functools import partial
import io

from utils import extract_text_from_file, image_to_base64, extract_grade
from engine import (
    detect_subject,
    grade_image_with_markup,
    judge_assignment,
    AllModelsFailedError,
)
from personas import PERSONAS
from report import create_pdf_report, create_marked_pdf
from storage import add_record, get_student_history
from rubrics import RUBRICS
from markup import draw_teacher_markup
from PIL import Image as PILImage

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

pn.extension(sizing_mode="stretch_width")

pn.config.raw_css.append("""
.markly-paper-pane {
    background: #F0EEE8;
    border-right: 1px solid #DDD;
    min-height: 100vh;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.markly-paper-shadow img {
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    border-radius: 3px;
}
.markly-controls-pane {
    background: #FAFAFA;
    padding: 24px 20px;
    min-height: 100vh;
}
.markly-grade {
    font-size: 28px;
    font-weight: bold;
    color: #C61E1E;
    text-align: center;
    margin: 8px 0;
}
.markly-status {
    background: #EEF4FF;
    border-left: 3px solid #1A5AC8;
    padding: 6px 12px;
    border-radius: 0 6px 6px 0;
    font-size: 13px;
    color: #1A5AC8;
    margin: 6px 0;
}
""")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# State holders for original / marked image bytes (PNG format)
# ---------------------------------------------------------------------------
_original_image_bytes = None
_marked_image_bytes = None

# ---------------------------------------------------------------------------
# UI Widgets
# ---------------------------------------------------------------------------
title = pn.pane.Markdown(
    "## Markly\n*AI-powered red-pen grading*",
    styles={"margin-bottom": "0"},
)

student_name = pn.widgets.TextInput(name="Student Name", placeholder="e.g. Alice Tan", width=320)
upload = pn.widgets.FileInput(accept=".pdf,.docx,.jpg,.jpeg,.png", width=320)
subject_select = pn.widgets.Select(name="Subject", options=list(PERSONAS.keys()), width=320)
grade_button = pn.widgets.Button(name="Grade Assignment", button_type="danger", width=320, height=44)

# --- Image preview widgets ---
paper_heading = pn.pane.Markdown(
    "### Assignment Preview\nUpload an image assignment to preview it here.",
    styles={"color": "#777", "margin-bottom": "12px"},
)

# Toggle to switch between original and marked
view_toggle = pn.widgets.RadioButtonGroup(
    options=["Original", "Marked"],
    value="Original",
    button_type="primary",
    visible=False,
    width=220,
)

# Placeholder when nothing uploaded
paper_placeholder = pn.pane.HTML(
    '<div style="'
    'width:520px; height:640px;'
    'border: 2px dashed #CCC;'
    'border-radius:8px;'
    'display:flex; align-items:center; justify-content:center;'
    'flex-direction:column; color:#AAA; font-size:15px;'
    'background: #FAF9F6;'
    '">'
    '<div style="font-size:48px; margin-bottom:12px;">&#128221;</div>'
    '<div>Upload an assignment to see it here</div>'
    '</div>',
    visible=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sanitize_student_name(name):
    """Sanitize student name for safe storage and display.

    Escapes HTML to prevent XSS when rendered in Markdown/HTML panes.
    """
    sanitized = "".join(ch for ch in name.strip() if ch.isprintable())
    return html.escape(sanitized[:100])


def _convert_to_png_bytes(file_bytes):
    """Convert any image format to PNG bytes for consistent display.

    Args:
        file_bytes: Raw image file bytes (JPEG, PNG, etc.)

    Returns:
        PNG-encoded bytes.
    """
    try:
        img = PILImage.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return buf.read()
    except Exception as exc:
        logger.warning("Failed to convert image to PNG: %s", exc)
        # Fallback: return original bytes as-is
        return file_bytes
    finally:
        try:
            img.close()
        except Exception:
            pass


def _get_image_to_display(upload_value, upload_filename, toggle_value):
    """Reactive function: return image bytes based on upload and toggle state.

    This is bound to the upload widget and toggle widget so it updates
    automatically whenever either changes. Returns PNG bytes that
    pn.pane.Image will render.
    """
    global _original_image_bytes, _marked_image_bytes

    if upload_value is None:
        # No file uploaded
        paper_placeholder.visible = True
        view_toggle.visible = False
        paper_heading.object = "### Assignment Preview\nUpload an image assignment to preview it here."
        return None

    filename_lower = (upload_filename or "").lower()
    is_image = filename_lower.endswith((".png", ".jpg", ".jpeg"))

    if not is_image:
        # Text file
        paper_placeholder.visible = True
        view_toggle.visible = False
        paper_heading.object = "### Assignment\n*" + html.escape(upload_filename) + "* (text-based, no visual preview)"
        return None

    # It is an image file
    paper_placeholder.visible = False

    # If we have not stored original yet, convert to PNG and store it
    if _original_image_bytes is None and upload_value is not None:
        _original_image_bytes = _convert_to_png_bytes(bytes(upload_value))

    # Determine which image to show
    if toggle_value == "Marked" and _marked_image_bytes is not None:
        paper_heading.object = "### Marked Assignment"
        return _marked_image_bytes
    else:
        paper_heading.object = "### Original Assignment\n*" + html.escape(upload_filename) + "*"
        return _original_image_bytes


# Create reactive image expression using pn.bind
reactive_image = pn.bind(
    _get_image_to_display,
    upload.param.value,
    upload.param.filename,
    view_toggle.param.value,
)

# Use pn.pane.Image with the reactive expression — Panel watches it and re-renders
image_display = pn.pane.Image(
    reactive_image,
    width=520,
    css_classes=["markly-paper-shadow"],
)

left_pane = pn.Column(
    paper_heading,
    pn.Row(view_toggle, align="center"),
    paper_placeholder,
    image_display,
    css_classes=["markly-paper-pane"], width=570, scroll=True
)

status = pn.pane.Markdown("", styles={"font-size": "13px"})
feedback = pn.pane.Markdown(
    "### Feedback\nGrade an assignment to see AI feedback here.",
    styles={"font-size": "14px", "line-height": "1.6"}
)
download = pn.widgets.FileDownload(
    label="Download Marked PDF", file=None,
    filename="marked_assignment.pdf", button_type="success",
    disabled=True, visible=False, width=320
)

# ---------------------------------------------------------------------------
# History Widgets
# ---------------------------------------------------------------------------
history_input = pn.widgets.TextInput(
    name="Lookup Student History", placeholder="Enter student name", width=320
)
history_button = pn.widgets.Button(name="View History", button_type="primary", width=320)
history_output = pn.pane.Markdown("", styles={"font-size": "13px", "margin-top": "8px"})

right_pane = pn.Column(
    title,
    pn.layout.Divider(),
    pn.pane.Markdown("**Student**"),
    student_name,
    pn.pane.Markdown("**Assignment**"),
    upload,
    pn.pane.Markdown("**Subject**"),
    subject_select,
    pn.Spacer(height=8),
    grade_button,
    status,
    pn.layout.Divider(),
    feedback,
    pn.Spacer(height=12),
    download,
    pn.layout.Divider(),
    pn.pane.Markdown("### Student History"),
    history_input,
    history_button,
    history_output,
    css_classes=["markly-controls-pane"],
    width=380,
    scroll=True,
)

# ---------------------------------------------------------------------------
# Main grading handler
# ---------------------------------------------------------------------------
async def grade_assignment(event):
    """Main grading pipeline handler."""
    global _original_image_bytes, _marked_image_bytes
    uploaded_bytes = upload.value
    uploaded_filename = upload.filename
    target_student = _sanitize_student_name(student_name.value)
    selected_subject = subject_select.value

    if uploaded_bytes is None or not target_student:
        feedback.object = (
            "### Missing input\n"
            "Please provide both a student name and an assignment file."
        )
        return

    if len(uploaded_bytes) > MAX_FILE_SIZE:
        feedback.object = (
            "### File too large\n"
            "Maximum file size is " + str(MAX_FILE_SIZE // (1024 * 1024)) + " MB."
        )
        return

    # Ensure original bytes are stored before grading starts
    filename_lower = uploaded_filename.lower()
    is_image = filename_lower.endswith((".png", ".jpg", ".jpeg"))
    if is_image and _original_image_bytes is None:
        _original_image_bytes = _convert_to_png_bytes(bytes(uploaded_bytes))

    # Clear any stale marked image from previous grading session
    _marked_image_bytes = None

    # Reset UI for grading
    download.disabled = True
    download.visible = False
    status.object = ""
    feedback.object = "### Feedback\nGrading in progress..."

    loop = asyncio.get_running_loop()

    try:
        if is_image:
            image_base64 = await loop.run_in_executor(
                None, partial(image_to_base64, uploaded_bytes)
            )
            content = "[IMAGE_ASSIGNMENT]"
        else:
            content = await loop.run_in_executor(
                None, partial(extract_text_from_file, uploaded_bytes, uploaded_filename)
            )

        # Subject detection
        predicted_subject, fallback_reason = await detect_subject(content)
        if predicted_subject not in PERSONAS:
            predicted_subject = selected_subject

        rubric = RUBRICS.get(predicted_subject, RUBRICS["Mathematics"])
        status_lines = ["Detected subject: <b>" + html.escape(predicted_subject) + "</b>"]
        if fallback_reason:
            status_lines.append(
                '<br><span style="color:#C61E1E;font-size:12px;">'
                + 'Subject detection unavailable -- using default. (' + html.escape(fallback_reason) + ')'
                + '</span>'
            )
        status.object = '<div class="markly-status">' + "".join(status_lines) + '</div>'

        if is_image:
            paper_heading.object = "### Grading in Progress...\nAI is annotating the paper..."

            try:
                markup_json_str = await grade_image_with_markup(image_base64, predicted_subject)
            except Exception as exc:
                error_msg = str(exc)
                logger.warning("Image grading API error: %s", error_msg)
                feedback.object = (
                    "### Grading Failed\n"
                    + "AI grading service returned an error: " + html.escape(error_msg) + "\n\n"
                    + "Please check your OpenRouter credits at https://openrouter.ai/settings/credits and try again."
                )
                return

            try:
                markup_data = json.loads(markup_json_str)
                if not isinstance(markup_data, dict):
                    markup_data = {}
            except json.JSONDecodeError:
                logger.warning("Failed to parse markup JSON")
                markup_data = {}

            overall_feedback_text = markup_data.get("overall_feedback", "No feedback provided.")
            grade_val = markup_data.get("grade", "N/A")
            marks = markup_data.get("marks", [])

            # Draw annotations
            marked_buf = await loop.run_in_executor(
                None, partial(draw_teacher_markup, uploaded_bytes, markup_json_str)
            )
            marked_buf.seek(0)
            # Store a DEEP COPY of marked image bytes (already PNG from draw_teacher_markup)
            _marked_image_bytes = bytes(marked_buf.read())

            # Enable toggle and switch to Marked view
            view_toggle.visible = True
            view_toggle.value = "Marked"
            paper_heading.object = "### Marked Assignment   `" + html.escape(grade_val) + "`"

            corrections = [m for m in marks if isinstance(m, dict) and m.get("type") == "correction"]

            # Re-create buffer for PDF from the stored bytes
            pdf_buf_source = io.BytesIO(_marked_image_bytes)
            pdf_buf = await loop.run_in_executor(
                None,
                partial(
                    create_marked_pdf,
                    student=target_student,
                    subject=predicted_subject,
                    filename=uploaded_filename,
                    marked_image_buffer=pdf_buf_source,
                    overall_feedback=overall_feedback_text,
                    grade=grade_val,
                    corrections=corrections,
                )
            )
            download.file = pdf_buf
            download.filename = "marked_" + uploaded_filename.rsplit(".", 1)[0] + ".pdf"
            download.label = "Download Marked Assignment (PDF)"

            # Build feedback text
            lines = ["**Grade: " + html.escape(grade_val) + "**"]
            if overall_feedback_text:
                lines += ["", overall_feedback_text]
            if corrections:
                lines += ["", "**Corrections:**"]
            for m in corrections:
                if m.get("text"):
                    lines.append("- " + m["text"])
            result = "\n".join(lines)

        else:
            # Text assignment
            feedback.object = "### Feedback\nEvaluating assignment..."
            try:
                result = await judge_assignment(content, rubric)
            except AllModelsFailedError:
                feedback.object = "### Grading Failed\nAll AI models failed. Please try again."
                return

            grade_val = extract_grade(result)

            pdf_buf = await loop.run_in_executor(
                None,
                partial(create_pdf_report, target_student, predicted_subject, uploaded_filename, result)
            )
            download.file = pdf_buf
            download.filename = "grading_report.pdf"
            download.label = "Download Grading Report (PDF)"
            paper_heading.object = "### Assignment\n_Text assignments don't have visual annotations._"

        feedback.object = "### Feedback\n" + result
        add_record(target_student.strip().lower(), predicted_subject, grade_val, result)
        download.disabled = False
        download.visible = True

    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        feedback.object = "### Error\n" + html.escape(str(exc))
    except asyncio.TimeoutError as exc:
        logger.error("Grading timed out: %s", exc)
        feedback.object = (
            "### Timeout\n"
            "The grading request timed out. Please try again with a smaller file or check your network connection."
        )
    except AllModelsFailedError as exc:
        logger.error("All AI models failed: %s", exc)
        feedback.object = (
            "### Grading Failed\n"
            "All AI models failed to produce a response. Please check your API credits and try again."
        )
    except Exception as exc:
        logger.exception("Unexpected error during grading")
        feedback.object = (
            "### Unexpected Error\n"
            + "An unexpected error occurred: " + html.escape(str(exc)) + "\n\n"
            + "Please check the logs or try again."
        )

    finally:
        # Ensure final heading state is set
        if is_image and _marked_image_bytes is not None:
            paper_heading.object = "### Marked Assignment   `" + html.escape(grade_val) + "`"


def lookup_history(event):
    """Fetch and display student grading history."""
    name = _sanitize_student_name(history_input.value)
    if not name:
        history_output.object = "Please enter a student name."
        return
    history = get_student_history(name.strip().lower())
    history_output.object = "**History for " + html.escape(name) + ":**\n\n" + history


# ---------------------------------------------------------------------------
# Wire up events
# ---------------------------------------------------------------------------
grade_button.on_click(grade_assignment)
history_button.on_click(lookup_history)

# Create app
app = pn.Row(left_pane, right_pane, sizing_mode="stretch_width")
app.servable(title="Markly - AI Grading Assistant")
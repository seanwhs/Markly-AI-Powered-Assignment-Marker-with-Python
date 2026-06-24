import panel as pn
import json

from utils import extract_text_from_file, image_to_base64
from engine import (
    detect_subject,
    extract_grade,
    grade_image_with_markup,
    judge_assignment,
)
from personas import PERSONAS
from report import create_pdf_report, create_marked_pdf
from storage import add_record, get_student_history
from rubrics import RUBRICS
from markup import draw_teacher_markup

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
.markly-paper-pane .bk-panel-models-pane-PaneBase {
    width: 100%;
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

title = pn.pane.Markdown(
    "## 🔴 Markly\n*AI-powered red-pen grading*",
    styles={"margin-bottom": "0"},
)

student_name = pn.widgets.TextInput(
    name="Student Name",
    placeholder="e.g. Alice Tan",
    width=320,
)
upload = pn.widgets.FileInput(
    accept=".pdf,.docx,.jpg,.jpeg,.png",
    width=320,
)
subject_select = pn.widgets.Select(
    name="Subject",
    options=list(PERSONAS.keys()),
    width=320,
)
grade_button = pn.widgets.Button(
    name="✦ Grade Assignment",
    button_type="danger",
    width=320,
    height=44,
)

paper_heading = pn.pane.Markdown(
    "### 📄 Marked Assignment\nUpload an assignment to see the annotated paper.",
    styles={"color": "#777", "margin-bottom": "12px"},
)
paper_preview = pn.pane.PNG(
    object=None,
    width=520,
    visible=False,
    css_classes=["markly-paper-shadow"],
)
paper_placeholder = pn.pane.Markdown(
    """
<div style="
    width:520px; height:640px;
    border: 2px dashed #CCC;
    border-radius:8px;
    display:flex; align-items:center; justify-content:center;
    flex-direction:column; color:#AAA; font-size:15px;
    background: #FAF9F6;
">
    <div style="font-size:48px; margin-bottom:12px;">📝</div>
    <div>Annotated paper will appear here</div>
</div>
""",
    visible=True,
)

left_pane = pn.Column(
    paper_heading,
    paper_placeholder,
    paper_preview,
    css_classes=["markly-paper-pane"],
    width=570,
    scroll=True,
)

status = pn.pane.Markdown("", styles={"font-size": "13px"})
feedback = pn.pane.Markdown(
    "### Feedback\nGrade an assignment to see AI feedback here.",
    styles={"font-size": "14px", "line-height": "1.6"},
)
download = pn.widgets.FileDownload(
    label="⬇ Download Marked PDF",
    file=None,
    filename="marked_assignment.pdf",
    button_type="success",
    disabled=True,
    visible=False,
    width=320,
)

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
    css_classes=["markly-controls-pane"],
    width=380,
    scroll=True,
)

async def grade_assignment(event):
    if upload.value is None or not student_name.value.strip():
        feedback.object = (
            "### ⚠️ Missing input\n"
            "Please upload an assignment **and** enter a student name."
        )
        return

    paper_preview.visible = False
    paper_preview.object = None
    paper_placeholder.visible = True
    paper_heading.object = "### 📄 Marked Assignment\n⏳ Processing…"
    download.disabled = True
    download.visible = False
    status.object = ""
    feedback.object = "### Feedback\n⏳ Grading in progress…"

    try:
        filename = upload.filename.lower()
        is_image = filename.endswith((".png", ".jpg", ".jpeg"))

        if is_image:
            image_base64 = image_to_base64(upload.value)
            content = "[IMAGE_ASSIGNMENT]"
        else:
            content = extract_text_from_file(upload.value, upload.filename)

        predicted_subject = await detect_subject(content)
        if predicted_subject not in PERSONAS:
            predicted_subject = subject_select.value

        rubric = RUBRICS.get(predicted_subject, "1. Overall Quality (10 points)")
        status.object = (
            f'<div class="markly-status">Detected subject: <b>{predicted_subject}</b></div>'
        )

        if is_image:
            paper_heading.object = "### 📄 Marked Assignment\n⏳ Annotating paper…"
            markup_json_str = await grade_image_with_markup(image_base64, predicted_subject)

            try:
                markup_data = json.loads(markup_json_str)
            except json.JSONDecodeError:
                markup_data = {}

            overall_feedback_text = markup_data.get("overall_feedback", "")
            grade_val = markup_data.get("grade", "N/A")
            marks = markup_data.get("marks", [])

            marked_buf = draw_teacher_markup(upload.value, markup_json_str)

            marked_buf.seek(0)
            paper_preview.object = marked_buf.read()
            paper_preview.visible = True
            paper_placeholder.visible = False
            paper_heading.object = f"### 📄 Marked Assignment   `{grade_val}`"

            corrections = [m for m in marks if m.get("type") == "correction"]
            marked_buf.seek(0)
            pdf_buf = create_marked_pdf(
                student=student_name.value,
                subject=predicted_subject,
                filename=upload.filename,
                marked_image_buffer=marked_buf,
                overall_feedback=overall_feedback_text,
                grade=grade_val,
                corrections=corrections,
            )
            download.file = pdf_buf
            download.filename = f"marked_{upload.filename.rsplit('.', 1)[0]}.pdf"
            download.label = "⬇ Download Marked Assignment (PDF)"

            lines = [f"**Grade: {grade_val}**"]
            if overall_feedback_text:
                lines += ["", overall_feedback_text]
            if corrections:
                lines += ["", "**Corrections:**"]
                for m in corrections:
                    if m.get("text"):
                        lines.append(f"- {m['text']}")
            result = "\n".join(lines)

        else:
            feedback.object = "### Feedback\n⏳ Evaluating assignment…"
            result = await judge_assignment(content, rubric)
            grade_val = extract_grade(result)

            pdf_buf = create_pdf_report(
                student=student_name.value,
                subject=predicted_subject,
                filename=upload.filename,
                feedback=result,
            )
            download.file = pdf_buf
            download.filename = "grading_report.pdf"
            download.label = "⬇ Download Grading Report (PDF)"

            paper_heading.object = (
                "### 📄 Assignment\n"
                "_Text assignments don't have visual annotations._"
            )

        feedback.object = f"### Feedback\n{result}"
        add_record(student_name.value, predicted_subject, grade_val, result)

        download.disabled = False
        download.visible = True

    except Exception:
        import traceback
        feedback.object = f"### ❌ Error\n```\n{traceback.format_exc()}\n```"
        download.disabled = True
        download.visible = False
        status.object = ""
        paper_heading.object = "### 📄 Marked Assignment"

grade_button.on_click(grade_assignment)

app = pn.Row(
    left_pane,
    right_pane,
    sizing_mode="stretch_width",
)

app.servable()
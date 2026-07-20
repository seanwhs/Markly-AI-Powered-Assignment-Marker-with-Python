import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.lib import colors

logger = logging.getLogger(__name__)
STYLES = getSampleStyleSheet()


def _make_styles():
    title_style = ParagraphStyle("Title2", parent=STYLES["Title"], spaceAfter=6 * mm)
    heading_style = ParagraphStyle("Heading2b", parent=STYLES["Heading2"], spaceBefore=6 * mm, spaceAfter=3 * mm)
    body_style = ParagraphStyle("Body2", parent=STYLES["Normal"], fontSize=11, leading=15, spaceAfter=3 * mm)
    return title_style, heading_style, body_style


def create_pdf_report(student: str, subject: str, filename: str, feedback: str) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    title_style, heading_style, body_style = _make_styles()

    story = [
        Paragraph(f"Grading Report - {student}", title_style),
        Paragraph(f"Subject: {subject}", body_style),
        Paragraph(f"File: {filename}", body_style),
        Spacer(1, 6 * mm),
        Paragraph(feedback.replace("\n", "<br/>"), body_style),
    ]
    doc.build(story)
    buf.seek(0)
    return buf


def create_marked_pdf(student: str, subject: str, filename: str,
                      marked_image_buffer: io.BytesIO,
                      overall_feedback: str, grade: str,
                      corrections: list, encouragement: str = "") -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    title_style, heading_style, body_style = _make_styles()

    story = [
        Paragraph(f"Marked Assignment - {student}", title_style),
        Paragraph(f"Subject: {subject}", body_style),
        Paragraph(f"File: {filename}", body_style),
        Spacer(1, 4 * mm),
    ]

    marked_image_buffer.seek(0)
    img = Image(marked_image_buffer, width=170 * mm, height=230 * mm)
    story.append(img)

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"Grade: {grade}", heading_style))

    if encouragement:
        story.append(Paragraph(f"<font color='#228B22'>{encouragement}</font>", body_style))
        story.append(Spacer(1, 3 * mm))

    if overall_feedback:
        story.append(Paragraph(overall_feedback.replace("\n", "<br/>"), body_style))

    if corrections:
        story.append(Paragraph("Corrections:", heading_style))
        items = []
        for c in corrections:
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            if text:
                items.append(ListItem(Paragraph(text, body_style)))
        if items:
            story.append(ListFlowable(items, bulletType="bullet", start=None,
                                       leftIndent=10 * mm))

    doc.build(story)
    buf.seek(0)
    return buf
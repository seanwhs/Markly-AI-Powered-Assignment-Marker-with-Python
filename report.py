# report.py  —  PDF generation for Markly
#
# create_marked_pdf  →  Page 1: annotated image  |  Page 2: structured teacher report
# create_pdf_report  →  Text-only report (for DOCX/PDF text assignments)

import io
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    HRFlowable, PageBreak, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Shared colour palette ─────────────────────────────────────────────────────
# Standard branding colours used for consistent UI/PDF visual identity
RED_INK    = colors.HexColor("#C61E1E")
DARK_GREY  = colors.HexColor("#2D2D2D")
MID_GREY   = colors.HexColor("#777777")
LIGHT_GREY = colors.HexColor("#DDDDDD")
CREAM      = colors.HexColor("#FFFEF5")
BLUE_INK   = colors.HexColor("#1A5AC8")


def _base_styles():
    """Initializes and configures the document paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "MarklyTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=DARK_GREY,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "MarklySubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=MID_GREY,
        spaceAfter=2,
        fontName="Helvetica-Oblique",
    ))
    styles.add(ParagraphStyle(
        "GradeStamp",
        parent=styles["Title"],
        textColor=RED_INK,
        fontSize=32,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=RED_INK,
        fontSize=13,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "BodyItalic",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        textColor=DARK_GREY,
        leading=16,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "TeacherComment",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#8B1A1A"),   # Deep red, mimicking ink pen
        fontSize=13,
        leading=20,
        leftIndent=12,
        rightIndent=12,
        borderPad=10,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "SmallMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=MID_GREY,
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=MID_GREY,
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
    ))
    return styles


def _meta_table(student, subject, filename, styles):
    """Generates a small metadata table for tracking assignment context."""
    data = [
        [Paragraph("<b>Student</b>", styles["SmallMeta"]),
         Paragraph(student, styles["BodyText"])],
        [Paragraph("<b>Subject</b>", styles["SmallMeta"]),
         Paragraph(subject, styles["BodyText"])],
        [Paragraph("<b>File</b>", styles["SmallMeta"]),
         Paragraph(filename, styles["SmallMeta"])],
    ]
    t = Table(data, colWidths=[38*mm, None])
    t.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("TOPPADDING",  (0,0), (-1,-1), 2),
    ]))
    return t


# ── Main: annotated image + structured report ─────────────────────────────────

def create_marked_pdf(
    student: str,
    subject: str,
    filename: str,
    marked_image_buffer: io.BytesIO,
    overall_feedback: str = "",
    grade: str = "",
    report_text: str = "",
    corrections: list[dict] | None = None,
) -> io.BytesIO:
    """
    Creates a two-page PDF:
    Page 1 displays the student's assignment image with AI annotations.
    Page 2 compiles the grading summary and detailed feedback into a report.
    """
    buffer = io.BytesIO()
    PAGE_W, PAGE_H = A4
    margin = 18 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=margin,
        bottomMargin=margin,
        leftMargin=margin,
        rightMargin=margin,
    )

    styles = _base_styles()
    story  = []

    # ── PAGE 1: Annotated Assignment ──────────────────────────────────────
    header_data = [
        [
            Paragraph(f"<b>{student}</b> — {subject}", styles["BodyText"]),
            Paragraph(
                f"Grade: <b>{grade}</b>" if grade and grade != "N/A" else "",
                ParagraphStyle("GradeInline", parent=styles["BodyText"],
                               textColor=RED_INK, fontName="Helvetica-Bold",
                               fontSize=13, alignment=TA_RIGHT)
            ),
        ]
    ]
    ht = Table(header_data, colWidths=[(PAGE_W - 2*margin)*0.65,
                                       (PAGE_W - 2*margin)*0.35])
    ht.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING",(0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("TOPPADDING",  (0,0), (-1,-1), 0),
    ]))
    story.append(ht)
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=1.5, color=RED_INK))
    story.append(Spacer(1, 8))

    # Add image, scaled to fit the page proportionally
    marked_image_buffer.seek(0)
    img_w = PAGE_W - 2 * margin
    img_h = PAGE_H - 2 * margin - 40
    rl_img = RLImage(
        marked_image_buffer,
        width=img_w,
        height=img_h,
        kind="proportional",
    )
    story.append(rl_img)

    # ── PAGE 2: Structured Teacher Report ────────────────────────────────
    story.append(PageBreak())

    story.append(Paragraph("Marked Assignment", styles["MarklyTitle"]))
    story.append(Paragraph(f"{student}  ·  {subject}", styles["MarklySubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=RED_INK))
    story.append(Spacer(1, 10))

    story.append(_meta_table(student, subject, filename, styles))
    story.append(Spacer(1, 14))

    # Optional Grade callout block
    if grade and grade.strip() not in ("", "N/A"):
        story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Grade: {grade}", styles["GradeStamp"]))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
        story.append(Spacer(1, 12))

    # Overall summary feedback
    if overall_feedback:
        story.append(Paragraph("Teacher's Comments", styles["SectionHeading"]))
        story.append(Paragraph(f'"{overall_feedback}"'.replace("\n", "<br/>"),
                                       styles["TeacherComment"]))
        story.append(Spacer(1, 10))

    # List of specific corrections or raw text feedback
    if corrections:
        story.append(Paragraph("Things to Fix", styles["SectionHeading"]))
        for item in corrections:
            txt = item.get("text", "")
            if txt:
                story.append(Paragraph(f"• {txt}", styles["BodyText"]))
        story.append(Spacer(1, 10))
    elif report_text:
        story.append(Paragraph("Things to Fix", styles["SectionHeading"]))
        story.append(Paragraph(report_text.replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 10))

    # Page footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Generated by Markly AI Grading Assistant",
                           styles["Footer"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Text-only report (PDF/DOCX assignments) ───────────────────────────────────

def create_pdf_report(student, subject, filename, feedback):
    """Generates a streamlined, text-focused PDF report for non-image assignments."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    styles = _base_styles()
    story  = []

    # Report Header
    story.append(Paragraph("Markly Grading Report", styles["MarklyTitle"]))
    story.append(Paragraph("AI-Powered Grading Assistant", styles["MarklySubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=RED_INK))
    story.append(Spacer(1, 12))

    story.append(_meta_table(student, subject, filename, styles))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
    story.append(Spacer(1, 10))

    # Main feedback content
    story.append(Paragraph(feedback.replace("\n", "<br/>"), styles["BodyText"]))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Generated by Markly AI Grading Assistant", styles["Footer"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
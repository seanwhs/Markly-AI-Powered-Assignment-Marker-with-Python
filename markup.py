# markup.py
"""Visual annotation engine for teacher-style markup on assignment images."""

import io
import random
import math
import textwrap
import os
from PIL import Image, ImageDraw, ImageFont
import logging
import json

logger = logging.getLogger(__name__)

_RNG = random.Random(42)
FONTS_DIR = "fonts"
FONT_CACHE = {}


def _get_font(size=24, bold=False):
    """Load handwriting font with multi-level fallback.

    Args:
        size: Font size in points.
        bold: Whether to prefer bold variant.

    Returns:
        PIL ImageFont instance.
    """
    key = (size, bold)
    if key in FONT_CACHE:
        return FONT_CACHE[key]

    candidates = []
    if bold:
        candidates.append(f"{FONTS_DIR}/Caveat-Bold.ttf")
    candidates.extend([
        f"{FONTS_DIR}/Caveat-Regular.ttf",
        f"{FONTS_DIR}/PatrickHand-Regular.ttf",
    ])

    # System font fallbacks
    system_fonts = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\times.ttf",
    ]
    candidates.extend(system_fonts)

    font = None
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue

    if font is None:
        font = ImageFont.load_default()

    FONT_CACHE[key] = font
    return font


def _jitter(val, amount=2.5):
    """Apply random offset to simulate handwriting variability."""
    return val + _RNG.uniform(-amount, amount)


def _jittered_line(draw, x1, y1, x2, y2, color="red", width=2, segments=8):
    """Draw wobbly hand-drawn line."""
    for i in range(segments):
        t1 = i / segments
        t2 = (i + 1) / segments
        px1 = _jitter(x1 + (x2 - x1) * t1)
        py1 = _jitter(y1 + (y2 - y1) * t1)
        px2 = _jitter(x1 + (x2 - x1) * t2)
        py2 = _jitter(y1 + (y2 - y1) * t2)
        draw.line((px1, py1, px2, py2), fill=color, width=width)


def _wavy_underline(draw, x1, y1, x2, y2, color="red", width=2, amplitude=5, wavelength=14):
    """Draw sinusoidal wavy underline."""
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1:
        return
    steps = max(int(length / 3), 10)
    points = []
    for i in range(steps + 1):
        t = i / steps
        bx = x1 + (x2 - x1) * t
        by = y1 + (y2 - y1) * t + math.sin(t * length / wavelength * 2 * math.pi) * amplitude
        points.append((_jitter(bx), _jitter(by)))
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)


def _wobbly_ellipse(draw, cx, cy, rx, ry, color="red", width=2):
    """Draw hand-drawn circle/ellipse with natural wobble."""
    points = []
    steps = 36
    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps
        r_wobble = 1.0 + _RNG.uniform(-0.07, 0.07)
        a_wobble = _RNG.uniform(-0.04, 0.04)
        px = cx + math.cos(angle + a_wobble) * rx * r_wobble
        py = cy + math.sin(angle + a_wobble) * ry * r_wobble
        points.append((_jitter(px, 1.5), _jitter(py, 1.5)))
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)


def _rounded_rect(draw, bbox, fill=None, outline="red", width=2, radius=8):
    """Draw rounded rectangle with proper corners."""
    xmin, ymin, xmax, ymax = bbox
    r = min(radius, (xmax - xmin) / 2, (ymax - ymin) / 2)

    draw.pieslice([xmin, ymin, xmin + r*2, ymin + r*2], 180, 270, fill=fill, outline=outline)
    draw.pieslice([xmax - r*2, ymin, xmax, ymin + r*2], 270, 360, fill=fill, outline=outline)
    draw.pieslice([xmin, ymax - r*2, xmin + r*2, ymax], 90, 180, fill=fill, outline=outline)
    draw.pieslice([xmax - r*2, ymax - r*2, xmax, ymax], 0, 90, fill=fill, outline=outline)

    if fill:
        draw.rectangle([xmin + r, ymin, xmax - r, ymax], fill=fill)
        draw.rectangle([xmin, ymin + r, xmax, ymax - r], fill=fill)

    draw.line([(xmin + r, ymin), (xmax - r, ymin)], fill=outline, width=width)
    draw.line([(xmin + r, ymax), (xmax - r, ymax)], fill=outline, width=width)
    draw.line([(xmin, ymin + r), (xmin, ymax - r)], fill=outline, width=width)
    draw.line([(xmax, ymin + r), (xmax, ymax - r)], fill=outline, width=width)


def _speech_bubble(draw, x, y, text, font, color="red"):
    """Draw speech bubble with wrapped text and pointer."""
    max_chars = 25
    lines = textwrap.wrap(text, width=max_chars) if text else []
    if not lines:
        lines = ["?"]

    line_h = font.size + 4
    box_w = max(len(l) for l in lines) * font.size * 0.55 + 20
    box_h = len(lines) * line_h + 16

    bx = x - box_w // 2
    by = y - box_h - 12
    if bx < 10:
        bx = 10
    if by < 10:
        by = y + 15

    for i, line in enumerate(lines):
        draw.text((bx + 10, by + 8 + i * line_h), line, fill=color, font=font)


def _draw_tick(draw, x, y, size=22, color="red"):
    """Draw natural checkmark."""
    x, y = _jitter(x, 1.5), _jitter(y, 1.5)
    _jittered_line(draw, x, y + size//2, x + size//3, y + size, color, 3, 4)
    _jittered_line(draw, x + size//3, y + size, x + size, y, color, 3, 5)


def _draw_cross(draw, x, y, size=24, color="red"):
    """Draw X mark."""
    x, y = _jitter(x, 1.5), _jitter(y, 1.5)
    offset = size // 2
    _jittered_line(draw, x - offset, y - offset, x + offset, y + offset, color, 3, 5)
    _jittered_line(draw, x + offset, y - offset, x - offset, y + offset, color, 3, 5)


def _draw_score_stamp(draw, x, y, grade_text, size=45):
    """Draw circular score stamp."""
    r = size // 2
    _wobbly_ellipse(draw, x, y, r, r, color="red", width=3)
    font = _get_font(size - 12, bold=True)
    bbox = font.getbbox(grade_text)
    tw = bbox[2] - bbox[0] if bbox else len(grade_text) * 10
    th = bbox[3] - bbox[1] if bbox else size - 12
    draw.text((x - tw//2, y - th//2), grade_text, fill="red", font=font)


def _draw_correction_box(draw, xmin, ymin, xmax, ymax, text=""):
    """Draw correction with wavy underline."""
    _wavy_underline(draw, xmin + 5, ymax - 10, xmax - 5, ymax - 10, color="red", width=2)
    if text:
        font = _get_font(16)
        draw.text((xmin + 6, ymin + 4), text, fill="red", font=font)


def _draw_praise_badge(draw, x, y, text, img_width):
    """Draw praise badge with text."""
    font = _get_font(17)
    lines = textwrap.wrap(text, width=20) if text else []
    if not lines:
        return

    line_h = 19
    box_w = max(len(l) for l in lines) * 10 + 16
    box_h = len(lines) * line_h + 10

    bx = x + 15
    if bx + box_w > img_width - 10:
        bx = x - box_w - 10

    by = y - box_h // 2
    if by < 10:
        by = 10

    for i, line in enumerate(lines):
        draw.text((bx + 8, by + 5 + i * line_h), line, fill="red", font=font)


def _draw_margin_note(draw, x, y, text, side="right", img_width=1000):
    """Draw wrapped margin note with connector."""
    font = _get_font(17)
    lines = textwrap.wrap(text, width=22) if text else []
    if not lines:
        return

    line_h = 20
    box_h = len(lines) * line_h + 12
    box_w = max(len(l) for l in lines) * 9 + 16

    if side == "right":
        bx = img_width - box_w - 15
    else:
        bx = 15

    by = y - box_h // 2
    if by < 5:
        by = 5
    if by + box_h > 2000:
        by = 2000 - box_h

    for i, line in enumerate(lines):
        draw.text((bx + 8, by + 6 + i * line_h), line, fill="red", font=font)

    if side == "right":
        _jittered_line(draw, bx, by + box_h//2, bx - 25, y, "red", 1, 4)
    else:
        _jittered_line(draw, bx + box_w, by + box_h//2, bx + box_w + 25, y, "red", 1, 4)


def _draw_summary_block(draw, x, y, text, img_width=1000):
    """Draw feedback block at bottom."""
    font = _get_font(18)
    lines = textwrap.wrap(text, width=70) if text else []
    if not lines:
        return

    line_h = 22
    box_h = len(lines) * line_h + 20
    box_w = min(img_width - 100, 700)

    for i, line in enumerate(lines):
        draw.text((x + 12, y + 10 + i * line_h), line, fill="red", font=font)


def _draw_encouragement_banner(draw, y, text, img_width):
    """Draw top encouragement banner."""
    font = _get_font(20, bold=True)
    lines = textwrap.wrap(text, width=50) if text else []
    if not lines:
        return

    line_h = 24
    box_h = len(lines) * line_h + 16
    box_w = min(img_width - 60, 600)
    x = (img_width - box_w) // 2

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0] if bbox else len(line) * 10
        draw.text((x + (box_w - tw)//2, y + 8 + i * line_h), line, fill="red", font=font)


def draw_teacher_markup(image_bytes: bytes, markup_json_str: str) -> io.BytesIO:
    """Draw rich teacher annotations on image and return PNG buffer.

    Args:
        image_bytes: Raw image file bytes.
        markup_json_str: JSON string with annotation instructions.

    Returns:
        BytesIO buffer containing the annotated PNG image.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(image)
        w, h = image.size

        data = {}
        try:
            data = json.loads(markup_json_str) if isinstance(markup_json_str, str) else markup_json_str
        except Exception as e:
            logger.warning("Failed to parse markup JSON: %s", e)

        if not isinstance(data, dict):
            data = {}

        marks = data.get("marks", [])
        scale = 1000.0

        used_y_positions = []

        def _find_clear_y(preferred_y, min_gap=30):
            y = preferred_y
            for _ in range(10):
                collision = any(abs(y - uy) < min_gap for uy in used_y_positions)
                if not collision:
                    used_y_positions.append(y)
                    return y
                y += min_gap
            return y

        for mark in marks:
            if not isinstance(mark, dict):
                continue

            mtype = mark.get("type", "")
            bbox = mark.get("bbox", [0, 0, 100, 100])
            text = mark.get("text", "")

            if len(bbox) != 4:
                continue

            try:
                ymin = max(0, min(1000, float(bbox[0]))) * h / scale
                xmin = max(0, min(1000, float(bbox[1]))) * w / scale
                ymax = max(0, min(1000, float(bbox[2]))) * h / scale
                xmax = max(0, min(1000, float(bbox[3]))) * w / scale
            except (ValueError, TypeError):
                continue

            if xmax <= xmin or ymax <= ymin:
                continue

            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2

            if mtype == "tick":
                _draw_tick(draw, cx, cy, color="red")
                if text:
                    ty = _find_clear_y(cy - 25)
                    _draw_praise_badge(draw, cx, ty, text, w)

            elif mtype == "cross":
                _draw_cross(draw, cx, cy, color="red")
                if text:
                    note_x = min(cx + 20, w - 120)
                    note_y = _find_clear_y(cy + 15)
                    font = _get_font(15)
                    draw.text((note_x + 4, note_y + 2), text[:30], fill="red", font=font)

            elif mtype == "correction":
                _draw_correction_box(draw, xmin, ymin, xmax, ymax, text)

            elif mtype == "comment":
                if text:
                    _speech_bubble(draw, cx, cy, text, _get_font(14), color="red")
                else:
                    _wobbly_ellipse(draw, cx, cy, (xmax-xmin)/2, (ymax-ymin)/2, color="red", width=2)

            elif mtype == "praise":
                _draw_tick(draw, cx, cy, color="red")
                if text:
                    ty = _find_clear_y(cy - 30)
                    _draw_praise_badge(draw, cx, ty, text, w)

            elif mtype == "margin_note" and text:
                _draw_margin_note(draw, cx, cy, text, side="right", img_width=w)

            elif mtype == "summary":
                pass

        overall = data.get("overall_feedback", "")
        if overall:
            fb_text = f"Teacher Feedback: {overall}"
            _draw_summary_block(draw, 40, h - 160, fb_text, img_width=w)

        grade = data.get("grade", "")
        if grade:
            _draw_score_stamp(draw, w - 70, 55, grade, size=50)

        encouragement = data.get("encouragement", "")
        if encouragement:
            _draw_encouragement_banner(draw, 15, encouragement, w)

        final = Image.new("RGB", image.size, (255, 255, 255))
        final.paste(image, mask=image.split()[3])
        buf = io.BytesIO()
        final.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.exception("Markup drawing failed, returning original image")
        buf = io.BytesIO(image_bytes)
        return buf
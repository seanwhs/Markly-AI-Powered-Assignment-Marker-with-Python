import io, json, math, os, random
from PIL import Image, ImageDraw, ImageFont

_FONT_CACHE: dict[tuple, ImageFont.FreeTypeFont] = {}

def _font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold, italic)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates = [
        "fonts/Caveat-Bold.ttf" if bold else "fonts/Caveat-Regular.ttf",
        "fonts/PatrickHand-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    f = ImageFont.load_default()
    for path in candidates:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                break
            except Exception:
                pass
    _FONT_CACHE[key] = f
    return f

RED = (198, 30, 30, 255)
RED_FILL = (198, 30, 30, 38)
BLUE = (30, 90, 200, 255)
BLUE_FILL = (30, 90, 200, 35)
GREEN = (25, 148, 55, 255)
GREEN_FILL = (25, 148, 55, 35)
ORANGE = (210, 120, 20, 255)
WHITE_SOLID = (255, 255, 255, 255)
BLACK = (20, 20, 20, 255)

def _jitter(val: float, amount: float = 2.5) -> float:
    return val + random.uniform(-amount, amount)

def _jittered_line(draw, x0, y0, x1, y1, fill, width=2, segments=6):
    pts = []
    for i in range(segments + 1):
        t = i / segments
        px = x0 + (x1 - x0) * t + (_jitter(0, 1.5) if 0 < i < segments else 0)
        py = y0 + (y1 - y0) * t + (_jitter(0, 1.5) if 0 < i < segments else 0)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=fill, width=width)

def _text_size(text: str, font) -> tuple[int, int]:
    try:
        bb = font.getbbox(text)
        return bb[2] - bb[0], bb[3] - bb[1]
    except Exception:
        return len(text) * max(8, getattr(font, 'size', 12) // 2), getattr(font, 'size', 12)

def _wavy_underline(draw, x0, y, x1, color, amplitude=5, wavelength=14):
    steps = max(int((x1 - x0) / 2), 2)
    pts = []
    for i in range(steps + 1):
        px = x0 + (x1 - x0) * i / steps
        py = y + amplitude * math.sin(2 * math.pi * i * (x1 - x0) / (steps * wavelength))
        pts.append((px, py))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=color, width=2)

def _wobbly_ellipse(draw, cx, cy, rx, ry, color, width=3, steps=60):
    pts = []
    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps
        wobble_r = random.uniform(0.93, 1.07)
        wobble_a = angle + random.uniform(-0.04, 0.04)
        px = cx + rx * wobble_r * math.cos(wobble_a) + _jitter(0, 1.2)
        py = cy + ry * wobble_r * math.sin(wobble_a) + _jitter(0, 1.2)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=color, width=width)

def _rounded_rect(draw, x0, y0, x1, y1, r, fill=None, outline=None, width=2):
    r = min(r, max(1, (x1-x0)//2), max(1, (y1-y0)//2))
    if fill:
        draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
        draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
        draw.pieslice([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill)
        draw.pieslice([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill)
        draw.pieslice([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill)
        draw.pieslice([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill)
    if outline:
        draw.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=outline, width=width)
        draw.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=outline, width=width)
        draw.line([x0+r, y0, x1-r, y0], fill=outline, width=width)
        draw.line([x0+r, y1, x1-r, y1], fill=outline, width=width)
        draw.line([x0, y0+r, x0, y1-r], fill=outline, width=width)
        draw.line([x1, y0+r, x1, y1-r], fill=outline, width=width)

def _speech_bubble(draw, ax, ay, text, color, font, img_w, img_h, pad=9):
    import textwrap
    max_chars = max(12, int(img_w * 0.20 / max(1, getattr(font, 'size', 12) * 0.55)))
    lines = textwrap.wrap(text, width=max_chars) or [text]
    line_h = getattr(font, 'size', 12) + 6
    tw = max(_text_size(l, font)[0] for l in lines)
    bw = tw + pad * 2
    bh = len(lines) * line_h + pad * 2
    tail = 12

    bx = min(ax, img_w - bw - 6)
    bx = max(bx, 4)
    by = ay - bh - tail
    flip_tail = by < 4
    if flip_tail:
        by = ay + tail + 4

    _rounded_rect(draw, bx+3, by+3, bx+bw+3, by+bh+3, 7, fill=(0,0,0,55))
    _rounded_rect(draw, bx, by, bx+bw, by+bh, 7, fill=WHITE_SOLID, outline=color, width=2)
    tail_tip = (ax, ay + (tail if flip_tail else 0))
    tail_base_y = by if flip_tail else by + bh
    draw.polygon([(bx+12, tail_base_y), (bx+24, tail_base_y), tail_tip], fill=WHITE_SOLID, outline=color)
    for i, line in enumerate(lines):
        draw.text((bx+pad, by+pad + i*line_h), line, fill=(*color[:3], 230), font=font)

def _draw_tick(draw, cx, cy, size, color):
    s = size * 0.38
    w = max(3, int(size // 9))
    p1 = (cx - s * 0.85 + _jitter(0,1), cy + _jitter(0,1))
    p2 = (cx - s * 0.15 + _jitter(0,1), cy + s * 0.65 + _jitter(0,1))
    p3 = (cx + s * 0.85 + _jitter(0,1), cy - s * 0.65 + _jitter(0,1))
    _jittered_line(draw, *p1, *p2, fill=color, width=w)
    _jittered_line(draw, *p2, *p3, fill=color, width=w)

def _draw_cross(draw, cx, cy, size, color):
    s = size * 0.38
    w = max(3, int(size // 9))
    _jittered_line(draw, cx-s, cy-s, cx+s, cy+s, fill=color, width=w)
    _jittered_line(draw, cx+s, cy-s, cx-s, cy+s, fill=color, width=w)

def _draw_score_stamp(draw, cx, cy, score_text, font_large, font_small, color, alpha_layer=None):
    parts = score_text.split("/")
    if len(parts) == 2 and alpha_layer:
        text = score_text
        tw, th = _text_size(text, font_large)
        bpad = 10
        bx0, by0 = int(cx - tw/2 - bpad), int(cy - th/2 - bpad)
        bx1, by1 = int(cx + tw/2 + bpad), int(cy + th/2 + bpad)
        ad = ImageDraw.Draw(alpha_layer)
        ad.rectangle([bx0, by0, bx1, by1], fill=(*color[:3], 25))
        _rounded_rect(draw, bx0, by0, bx1, by1, 6, outline=color, width=3)
        draw.text((int(cx - tw/2), int(cy - th/2)), text, fill=color, font=font_large)
    else:
        r = max(28, getattr(font_large, 'size', 20) + 14)
        _wobbly_ellipse(draw, int(cx), int(cy), r, r, color, width=3)
        if len(parts) == 2:
            tw, th = _text_size(parts[0], font_large)
            draw.text((int(cx - tw/2), int(cy - th - 2)), parts[0], fill=color, font=font_large)
            st = "/" + parts[1]
            sw, sh = _text_size(st, font_small)
            draw.text((int(cx - sw/2), int(cy + 2)), st, fill=color, font=font_small)
        else:
            tw, th = _text_size(score_text, font_large)
            draw.text((int(cx - tw/2), int(cy - th/2)), score_text, fill=color, font=font_large)

def _draw_correction_box(draw, left, top, right, bottom, color, alpha_layer):
    ad = ImageDraw.Draw(alpha_layer)
    _rounded_rect(ad, int(left), int(top), int(right), int(bottom), 6, fill=(*color[:3], 35))
    _rounded_rect(draw, int(left), int(top), int(right), int(bottom), 6, outline=color, width=3)
    _wavy_underline(draw, left, bottom + 5, right, color)

def _draw_comment_box(draw, left, top, right, bottom, color):
    dash, gap = 10, 5
    total = dash + gap
    def _dashes(x0, y0, x1, y1, horiz):
        length = abs(x1-x0) if horiz else abs(y1-y0)
        for i in range(int(length / total) + 1):
            s = i * total; e = min(s + dash, length)
            if horiz:
                draw.line([(x0+s, y0), (x0+e, y0)], fill=color, width=2)
            else:
                draw.line([(x0, y0+s), (x0, y0+e)], fill=color, width=2)
    _dashes(left, top, right, top, True)
    _dashes(left, bottom, right, bottom, True)
    _dashes(left, top, left, bottom, False)
    _dashes(right, top, right, bottom, False)

def _draw_margin_note(draw, img_w, img_h, text, y_pos, color, font, side="right"):
    import textwrap
    margin_x = int(img_w * 0.02) if side == "left" else int(img_w * 0.75)
    max_width = int(img_w * 0.22)
    max_chars = max(8, int(max_width / max(1, getattr(font, 'size', 12) * 0.55)))
    lines = textwrap.wrap(text, width=max_chars) or [text]
    line_h = getattr(font, 'size', 12) + 4
    bh = len(lines) * line_h + 8
    draw.rectangle([margin_x - 4, y_pos - 4, margin_x + max_width + 4, y_pos + bh], fill=(*color[:3], 18))
    for i, line in enumerate(lines):
        draw.text((margin_x, y_pos + i * line_h), line, fill=(*color[:3], 210), font=font)
    if side == "right":
        ax = margin_x - 8
        ay = y_pos + bh // 2
        draw.polygon([(ax, ay), (ax+10, ay-5), (ax+10, ay+5)], fill=color)

def _draw_summary_block(draw, img_w, img_h, summary_text, font, color):
    import textwrap
    block_top = int(img_h * 0.80)
    pad = 14
    max_width = int(img_w * 0.90)
    margin_x = int(img_w * 0.05)
    fs = getattr(font, 'size', 14)
    max_chars = max(20, int(max_width / (fs * 0.58)))
    lines = textwrap.wrap(summary_text, width=max_chars) or [summary_text]
    line_h = fs + 5
    block_h = len(lines) * line_h + pad * 2 + 8
    draw.rectangle([margin_x - pad, block_top - 4, margin_x + max_width + pad, block_top + block_h], fill=(255, 252, 200, 60))
    _jittered_line(draw, margin_x - pad, block_top - 4, margin_x + max_width + pad, block_top - 4, fill=color, width=2)
    for i, line in enumerate(lines):
        draw.text((margin_x, block_top + pad + i * line_h), line, fill=(*color[:3], 215), font=font)

def draw_teacher_markup(image_bytes: bytes, markup_json: str) -> io.BytesIO:
    random.seed(42)
    base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W, H = base.size

    try:
        data = json.loads(markup_json)
    except json.JSONDecodeError:
        data = {"marks": []}

    marks = data.get("marks", [])
    if len(marks) < 15:
        marks.append({
            "type": "comment",
            "bbox": [10, 10, 30, 200],
            "text": "Check working"
        })

    grade = data.get("grade", "")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    alpha_fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    base_sz = max(18, min(H // 26, 52))
    f_comment = _font(base_sz, italic=True)
    f_stamp = _font(int(base_sz * 1.25), bold=True)
    f_stamp_s = _font(int(base_sz * 0.85))
    f_praise = _font(int(base_sz * 1.45), bold=True)
    f_margin = _font(int(base_sz * 0.82), italic=True)
    f_summary = _font(int(base_sz * 0.90), italic=True)

    for mark in marks:
        try:
            ymin, xmin, ymax, xmax = mark["bbox"]
        except (KeyError, ValueError, TypeError):
            continue

        left = xmin / 1000 * W
        top = ymin / 1000 * H
        right = xmax / 1000 * W
        bottom = ymax / 1000 * H
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        size = max(right - left, bottom - top)

        mtype = mark.get("type", "comment")
        text = mark.get("text", "")

        if mtype == "tick":
            _draw_tick(draw, cx, cy, size, GREEN)
            if text and text.lower() not in ("correct", "✓", "", "right"):
                _speech_bubble(draw, cx, top, text, GREEN, f_comment, W, H)
        elif mtype == "cross":
            _draw_cross(draw, cx, cy, size, RED)
            if text:
                _speech_bubble(draw, cx, top, text, RED, f_comment, W, H)
        elif mtype == "score":
            _draw_score_stamp(draw, int(cx), int(cy), text, f_stamp, f_stamp_s, RED, alpha_fill)
        elif mtype == "praise":
            tw, th = _text_size(text, f_praise)
            tx = int(cx - tw / 2)
            ty = int(cy - th / 2)
            draw.text((tx + _jitter(0,1), ty + _jitter(0,1)), text, fill=RED, font=f_praise)
            _wavy_underline(draw, tx, ty + th + 5, tx + tw, RED, amplitude=4)
        elif mtype == "correction":
            _draw_correction_box(draw, left, top, right, bottom, RED, alpha_fill)
            if text:
                _speech_bubble(draw, left, top, text, RED, f_comment, W, H)
        elif mtype == "comment":
            _draw_comment_box(draw, left, top, right, bottom, BLUE)
            if text:
                _speech_bubble(draw, right, top, text, BLUE, f_comment, W, H)
        elif mtype == "margin_note":
            side = "left" if cx > W * 0.5 else "right"
            _draw_margin_note(draw, W, H, text, int(top), ORANGE, f_margin, side)
            ptr_x = int(W * 0.73) if side == "right" else int(W * 0.27)
            _jittered_line(draw, ptr_x, int(cy), int(cx), int(cy), fill=(*ORANGE[:3], 140), width=1)
        elif mtype == "summary":
            _draw_summary_block(draw, W, H, text, f_summary, BLUE)

    if grade and grade.strip() not in ("", "N/A"):
        pad_x = max(70, int(W * 0.10))
        pad_y = max(70, int(H * 0.06))
        gx = W - pad_x
        gy = H - pad_y
        _draw_score_stamp(draw, gx, gy, grade, f_stamp, f_stamp_s, RED, alpha_fill)

    result = Image.alpha_composite(base, alpha_fill)
    result = Image.alpha_composite(result, overlay)
    result = result.convert("RGB")

    out = io.BytesIO()
    result.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out
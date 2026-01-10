from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def render_classic_pdf(data: Dict[str, Any]) -> bytes:
    """
    Classic (current) PDF renderer.
    Produces a cover-letter style layout with:
    - Left block: date + company + location + job title
    - Right block: CONTACT INFO heading + phone/email/location rows
    - Body: justified paragraphs
    """
    if not isinstance(data, dict):
        raise TypeError("render_classic_pdf expects a dict")

    extracted = data.get("extracted") or {}
    cover = data.get("cover_letter") or {}
    paragraphs = cover.get("paragraphs") or []

    applicant_name = _clean(extracted.get("applicant_name"))
    applicant_email = _clean(extracted.get("applicant_email"))
    applicant_phone = _clean(extracted.get("applicant_phone"))
    applicant_address = _clean(extracted.get("applicant_address"))
    applicant_role = _clean(extracted.get("applicant_status_or_role"))

    company_name = _clean(extracted.get("company_name"))
    company_location = _clean(extracted.get("company_location"))
    hiring_manager = _clean(extracted.get("hiring_manager_name")) or "Hiring Manager"
    job_title = _clean(extracted.get("job_title"))

    # --- Canvas ---
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)

    page_w, page_h = LETTER

    # Content block centered like Overleaf
    CONTENT_WIDTH = 6.5 * inch
    x0 = (page_w - CONTENT_WIDTH) / 2

    top_margin = 1.0 * inch
    bottom_margin = 1.0 * inch
    y = page_h - top_margin
    bottom_y = bottom_margin

    # Typography
    FONT_BODY = "Times-Roman"
    FONT_BOLD = "Times-Bold"

    SIZE_NAME = 22
    SIZE_ROLE = 9.5
    SIZE_BODY = 12
    SIZE_SECTION = 12

    LEADING = 15

    HEADING_GRAY = colors.HexColor("#4D4D4D")
    SUBTLE_GRAY = colors.HexColor("#777777")

    def new_page():
        nonlocal y
        c.showPage()
        y = page_h - top_margin

    def ensure_space(px: float):
        if y - px <= bottom_y:
            new_page()

    def draw_line_gap(mult: float = 1.0):
        nonlocal y
        y -= LEADING * mult

    # -----------------------------
    # HEADER (name + role)
    # -----------------------------
    ensure_space(80)

    if applicant_name:
        c.setFont(FONT_BOLD, SIZE_NAME)
        c.setFillColor(HEADING_GRAY)
        c.drawString(x0, y, applicant_name)
        y -= 28

    if applicant_role:
        c.setFont(FONT_BODY, SIZE_ROLE)
        c.setFillColor(SUBTLE_GRAY)
        c.drawString(x0, y, applicant_role.upper())
        y -= 20

    draw_line_gap(0.7)

    # -----------------------------
    # TWO COLUMN TOP BLOCK
    # -----------------------------
    left_w = CONTENT_WIDTH * 0.56
    right_w = CONTENT_WIDTH * 0.40
    gap = CONTENT_WIDTH - left_w - right_w

    x_left = x0
    x_right = x0 + left_w + gap

    block_top = y
    ensure_space(160)

    # LEFT: date + company + location + title
    left_lines: List[str] = [_today_string()]
    if company_name:
        left_lines.append(company_name)
    if company_location:
        left_lines.append(company_location)
    if job_title:
        left_lines.append(job_title)

    yy_left = block_top
    for i, ln in enumerate(left_lines):
        font = FONT_BOLD if i == 0 else FONT_BODY
        size = SIZE_SECTION if i == 0 else SIZE_BODY
        c.setFont(font, size)
        c.setFillColor(colors.black)
        for w in _wrap_text(c, ln, left_w, font, size):
            c.drawString(x_left, yy_left, w)
            yy_left -= LEADING

    # RIGHT: grouped CONTACT INFO block
    yy_right = block_top

    CONTACT_BLOCK_W = right_w * 0.92
    x_contact = x_right + (right_w - CONTACT_BLOCK_W) / 2

    label_w = CONTACT_BLOCK_W * 0.34
    value_w = CONTACT_BLOCK_W - label_w
    label_x = x_contact
    value_x = x_contact + label_w

    heading = "CONTACT INFO"
    c.setFont(FONT_BOLD, SIZE_SECTION)
    c.setFillColor(HEADING_GRAY)

    heading_x = x_contact
    c.drawString(heading_x, yy_right, heading)
    yy_right -= (LEADING + 6)

    rows: List[Tuple[str, str]] = []
    if applicant_phone:
        rows.append(("Phone", applicant_phone))
    if applicant_email:
        rows.append(("Email", applicant_email))

    loc = ""
    if applicant_address:
        loc = applicant_address.splitlines()[0].strip()
    if loc:
        rows.append(("Location", loc))

    for label, value in rows:
        c.setFont(FONT_BODY, SIZE_ROLE)
        c.setFillColor(SUBTLE_GRAY)
        c.drawString(label_x, yy_right, label)

        c.setFillColor(colors.black)
        wrapped = _wrap_text(c, value, value_w, FONT_BODY, SIZE_ROLE)
        first = True
        for w in wrapped:
            if first:
                c.drawString(value_x, yy_right, w)
                first = False
            else:
                yy_right -= LEADING
                c.drawString(value_x, yy_right, w)

        yy_right -= LEADING

    # Continue below whichever column ended lower
    y = min(yy_left, yy_right) - 26

    # -----------------------------
    # BODY
    # -----------------------------
    ensure_space(260)

    c.setFont(FONT_BOLD, SIZE_SECTION)
    c.setFillColor(colors.black)
    c.drawString(x0, y, f"DEAR {hiring_manager.upper()}")
    y -= (LEADING + 10)

    if not isinstance(paragraphs, list):
        paragraphs = []

    for p in paragraphs[:3]:
        p = _clean(p)
        if not p:
            continue

        ensure_space(120)
        y = _draw_justified_paragraph(
            c=c,
            text=p,
            x=x0,
            y=y,
            max_width=CONTENT_WIDTH,
            font=FONT_BODY,
            size=SIZE_BODY,
            leading=LEADING,
            bottom_y=bottom_y,
            new_page=new_page,
            top_y=lambda: page_h - top_margin,
        )
        y -= 10

    # Sign-off
    ensure_space(90)
    c.setFont(FONT_BODY, SIZE_BODY)
    c.setFillColor(colors.black)
    c.drawString(x0, y, "Sincerely,")
    y -= (LEADING + 18)

    if applicant_name:
        c.drawString(x0, y, applicant_name)

    c.save()
    buf.seek(0)
    return buf.getvalue()


# Optional backwards-compatible alias (remove later once you update imports)
cover_letter_text_to_pdf_bytes = render_classic_pdf


# -----------------------------
# Helpers
# -----------------------------
def _clean(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _today_string() -> str:
    return date.today().strftime("%d/%m/%Y")


def _wrap_text(c: canvas.Canvas, text: str, max_width: float, font: str, size: float) -> List[str]:
    out: List[str] = []
    for raw in str(text).splitlines():
        words = raw.split()
        if not words:
            out.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            test = f"{cur} {w}"
            if c.stringWidth(test, font, size) <= max_width:
                cur = test
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def _draw_justified_paragraph(
    *,
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font: str,
    size: float,
    leading: float,
    bottom_y: float,
    new_page,
    top_y,
) -> float:
    c.setFont(font, size)
    c.setFillColor(colors.black)

    raw_lines = str(text).splitlines() or [str(text)]
    space_w = c.stringWidth(" ", font, size)

    for para_idx, raw in enumerate(raw_lines):
        words = raw.split()
        if not words:
            y -= leading
            continue

        line_words: List[str] = []
        line_width = 0.0

        def flush_line(justify: bool):
            nonlocal y, line_words, line_width

            if y - leading <= bottom_y:
                new_page()
                y = top_y()

            if not line_words:
                y -= leading
                return

            if not justify or len(line_words) == 1:
                c.drawString(x, y, " ".join(line_words))
                y -= leading
            else:
                words_w = sum(c.stringWidth(w, font, size) for w in line_words)
                gaps = len(line_words) - 1
                extra = max_width - words_w
                gap_w = extra / gaps if gaps > 0 else space_w

                cx = x
                for i, w in enumerate(line_words):
                    c.drawString(cx, y, w)
                    cx += c.stringWidth(w, font, size)
                    if i < gaps:
                        cx += gap_w
                y -= leading

            line_words = []
            line_width = 0.0

        for w in words:
            w_w = c.stringWidth(w, font, size)
            if not line_words:
                line_words = [w]
                line_width = w_w
            else:
                test_width = line_width + space_w + w_w
                if test_width <= max_width:
                    line_words.append(w)
                    line_width = test_width
                else:
                    flush_line(justify=True)
                    line_words = [w]
                    line_width = w_w

        flush_line(justify=False)

        if para_idx < len(raw_lines) - 1:
            y -= leading * 0.25

    return y

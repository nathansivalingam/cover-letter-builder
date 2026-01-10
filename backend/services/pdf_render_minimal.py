from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any, Dict, List

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def render_minimal_pdf(data: Dict[str, Any]) -> bytes:
    """
    Minimal cover letter renderer:
    - Contact block at top-left
    - Company on left + date on right
    - Salutation line (drawn once here)
    - Justified paragraphs (last line left-aligned)
    """
    if not isinstance(data, dict):
        raise TypeError("render_minimal_pdf expects a dict")

    extracted = data.get("extracted") or {}
    cover = data.get("cover_letter") or {}
    paragraphs = cover.get("paragraphs") or []

    applicant_name = _clean(extracted.get("applicant_name"))
    applicant_email = _clean(extracted.get("applicant_email"))
    applicant_phone = _clean(extracted.get("applicant_phone"))
    applicant_address = _clean(extracted.get("applicant_address"))

    company_name = _clean(extracted.get("company_name"))
    hiring_manager = _clean(extracted.get("hiring_manager_name")) or "Hiring Manager"

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    page_w, page_h = LETTER

    left_margin = 1.0 * inch
    right_margin = 1.0 * inch
    top_margin = 1.0 * inch
    bottom_margin = 1.0 * inch

    x0 = left_margin
    x1 = page_w - right_margin
    y = page_h - top_margin

    FONT = "Times-Roman"
    FONT_BOLD = "Times-Bold"
    SIZE = 10
    LEADING = 12  # tighter so it stays on one page more often

    def new_page():
        nonlocal y
        c.showPage()
        y = page_h - top_margin

    def ensure_space(px: float):
        if y - px <= bottom_margin:
            new_page()

    # -----------------------------
    # Contact block (top-left)
    # -----------------------------
    ensure_space(80)

    if applicant_name:
        c.setFont(FONT, SIZE)
        c.drawString(x0, y, applicant_name)
        y -= LEADING

    c.setFont(FONT, SIZE)
    for line in _contact_lines(applicant_address, applicant_email, applicant_phone):
        c.drawString(x0, y, line)
        y -= LEADING

    y -= LEADING * 1.5  # was 1.5

    # -----------------------------
    # Company (left) + Date (right)
    # -----------------------------
    ensure_space(40)

    date_right = date.today().strftime("%d.%m.%Y")
    if company_name:
        c.drawString(x0, y, f"{company_name},")
    c.drawRightString(x1, y, date_right)
    y -= LEADING * 4.5  # was 2

    # -----------------------------
    # Salutation
    # -----------------------------
    ensure_space(40)
    c.setFont(FONT, SIZE)
    c.drawString(x0, y, f"Dear {hiring_manager},")
    y -= LEADING * 2  # was 2

    # -----------------------------
    # Body paragraphs (justified)
    # -----------------------------
    if not isinstance(paragraphs, list):
        paragraphs = []

    for i, p in enumerate(paragraphs[:3]):
        p = _clean(p)
        if not p:
            continue

        # If the model included "Dear ...," in paragraph 1, strip it so we don't double-salute
        if i == 0:
            p = _strip_salutation(p)
            if not p:
                continue

        ensure_space(110)

        y = _draw_justified_paragraph(
            c=c,
            text=p,
            x=x0,
            y=y,
            max_width=(x1 - x0),
            font=FONT,
            size=SIZE,
            leading=LEADING,
            bottom_y=bottom_margin,
            new_page=new_page,
            top_y=lambda: page_h - top_margin,
        )

        y -= LEADING

    # -----------------------------
    # Sign-off
    # -----------------------------
    ensure_space(80)
    c.drawString(x0, y, "Sincerely,")
    y -= LEADING * 1.5

    if applicant_name:
        c.drawString(x0, y, applicant_name)

    c.save()
    buf.seek(0)
    return buf.getvalue()


def _clean(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _strip_salutation(p: str) -> str:
    """
    Remove a leading 'Dear ...,' line if the model put it into the first paragraph.
    """
    s = p.strip()
    lower = s.lower()
    if lower.startswith("dear "):
        comma = s.find(",")
        if comma != -1:
            return s[comma + 1 :].strip()
        nl = s.find("\n")
        if nl != -1:
            return s[nl + 1 :].strip()
        return ""
    return s


def _contact_lines(address: str, email: str, phone: str) -> List[str]:
    lines: List[str] = []
    if address:
        for ln in str(address).splitlines():
            ln = ln.strip()
            if ln:
                lines.append(ln)
    if email:
        lines.append(email)
    if phone:
        lines.append(phone)
    return lines


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
    """
    Draw a paragraph with full justification (except last line).
    Returns updated y.
    """
    c.setFont(font, size)

    space_w = c.stringWidth(" ", font, size)
    words = str(text).split()
    if not words:
        return y - leading

    line_words: List[str] = []
    line_width = 0.0

    def flush(justify: bool):
        nonlocal y, line_words, line_width

        if y - leading <= bottom_y:
            new_page()
            y = top_y()

        if not line_words:
            y -= leading
            return

        if not justify or len(line_words) == 1:
            c.drawString(x, y, " ".join(line_words))
        else:
            words_w = sum(c.stringWidth(w, font, size) for w in line_words)
            gaps = len(line_words) - 1
            extra = max_width - words_w
            gap_w = extra / gaps if gaps else space_w

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
                flush(justify=True)
                line_words = [w]
                line_width = w_w

    flush(justify=False)
    return y

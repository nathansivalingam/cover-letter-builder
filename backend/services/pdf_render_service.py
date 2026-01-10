from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Any, Dict, List, Tuple

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas


# -----------------------------
# Public API (keep name the same)
# -----------------------------
def cover_letter_text_to_pdf_bytes(data: Dict[str, Any]) -> bytes:
    """
    DICT-ONLY PDF renderer.

    Expects structured data like:
    {
      "extracted": {
        "applicant_name": ...,
        "applicant_email": ...,
        "applicant_phone": ...,
        "applicant_address": ...,
        "applicant_status_or_role": ...,
        "company_name": ...,
        "company_location": ...,
        "hiring_manager_name": ...,
        "job_title": ...
      },
      "cover_letter": {"paragraphs": [p1, p2, p3]},
      "missing_info_questions": [...]
    }
    """
    if not isinstance(data, dict):
        raise TypeError("cover_letter_text_to_pdf_bytes expects a dict")

    extracted = data.get("extracted") or {}
    cover = data.get("cover_letter") or {}
    paragraphs = cover.get("paragraphs") or []

    if not isinstance(extracted, dict):
        extracted = {}
    if not isinstance(cover, dict):
        cover = {}
    if not isinstance(paragraphs, list):
        paragraphs = []

    # Pull fields (clean + defaults)
    applicant_name = _clean(extracted.get("applicant_name"))
    applicant_email = _clean(extracted.get("applicant_email"))
    applicant_phone = _clean(extracted.get("applicant_phone"))
    applicant_address = _clean(extracted.get("applicant_address"))
    applicant_role = _clean(extracted.get("applicant_status_or_role"))

    company_name = _clean(extracted.get("company_name"))
    company_location = _clean(extracted.get("company_location"))
    hiring_manager = _clean(extracted.get("hiring_manager_name")) or "Hiring Manager"
    job_title = _clean(extracted.get("job_title"))

    # If applicant_address is one line like "Baulkham Hills, NSW", keep it.
    # If it's multiline, we keep lines.

    # Build PDF
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)

    # Page geometry
    width, height = LETTER
    margin_l = 1.0 * inch
    margin_r = 1.0 * inch
    margin_t = 1.0 * inch
    margin_b = 1.0 * inch

    content_w = width - margin_l - margin_r
    top_y = height - margin_t
    bottom_y = margin_b

    # Typography
    FONT_BODY = "Times-Roman"
    FONT_BOLD = "Times-Bold"
    SIZE_BODY = 11.5
    SIZE_NAME = 18
    SIZE_ROLE = 9.5
    SIZE_SECTION = 10.5

    LINE = 14  # baseline line height

    # Colors (approx your LaTeX template greys)
    HEADING_GRAY = colors.HexColor("#4D4D4D")
    SUBTLE_GRAY = colors.HexColor("#777777")

    y = top_y

    def new_page():
        nonlocal y
        c.showPage()
        y = top_y

    def ensure_space(px_needed: float):
        nonlocal y
        if y - px_needed <= bottom_y:
            new_page()

    def draw_wrapped(
        text: str,
        x: float,
        y_start: float,
        max_width: float,
        font: str,
        size: float,
        color=colors.black,
        leading: float = LINE,
    ) -> Tuple[float, int]:
        """
        Draw wrapped text starting at (x, y_start).
        Returns (new_y, lines_drawn).
        """
        if text is None:
            return y_start, 0

        text = str(text).strip()
        if text == "":
            return y_start - leading, 1  # blank line

        c.setFont(font, size)
        c.setFillColor(color)

        lines = _wrap_text(c, text, max_width, font, size)
        yy = y_start
        for ln in lines:
            yy -= 0  # keep explicit
            c.drawString(x, yy, ln)
            yy -= leading
        return yy, len(lines)

    # -----------------------------
    # Header: Name + role
    # -----------------------------
    if applicant_name:
        ensure_space(40)
        c.setFont(FONT_BOLD, SIZE_NAME)
        c.setFillColor(HEADING_GRAY)
        c.drawString(margin_l, y, applicant_name)
        y -= 22

    if applicant_role:
        ensure_space(18)
        c.setFont(FONT_BODY, SIZE_ROLE)
        c.setFillColor(SUBTLE_GRAY)
        c.drawString(margin_l, y, applicant_role.upper())
        y -= 18

    # Space after header
    y -= 10

    # -----------------------------
    # Two-column top block:
    # Left: date + company + location (+ optional job title)
    # Right: CONTACT INFO table-like
    # -----------------------------
    left_w = content_w * 0.56
    right_w = content_w * 0.40
    gap = content_w - left_w - right_w
    x_left = margin_l
    x_right = margin_l + left_w + gap

    # Compute block height by drawing manually line-by-line
    # We'll draw from current y downward, but in two columns, then set y to the lower of both.
    y_block_top = y

    # Left column lines
    left_lines: List[str] = []
    left_lines.append(_today_string())
    if company_name:
        left_lines.append(company_name)
    if company_location:
        left_lines.append(company_location)
    if job_title:
        left_lines.append(job_title)

    # Draw left column
    yy_left = y_block_top
    ensure_space(120)
    for i, ln in enumerate(left_lines):
        if i == 0:
            # Date in bold
            c.setFont(FONT_BOLD, SIZE_SECTION)
            c.setFillColor(colors.black)
        else:
            c.setFont(FONT_BODY, SIZE_BODY)
            c.setFillColor(colors.black)

        # Wrap each line to left column width
        wrapped = _wrap_text(c, ln, left_w, c._fontname, c._fontsize)
        for wln in wrapped:
            c.drawString(x_left, yy_left, wln)
            yy_left -= LINE

    # Right column: heading + label/value rows
    yy_right = y_block_top

    # CONTACT INFO heading
    c.setFont(FONT_BOLD, SIZE_SECTION)
    c.setFillColor(HEADING_GRAY)
    # "heading aligned right" vibe: place heading at right edge by measuring width
    heading = "CONTACT INFO"
    heading_w = c.stringWidth(heading, FONT_BOLD, SIZE_SECTION)
    c.drawString(x_right + right_w - heading_w, yy_right, heading)
    yy_right -= (LINE + 4)

    # Rows: Phone / Email / Location (address)
    rows: List[Tuple[str, str]] = []
    if applicant_phone:
        rows.append(("Phone", applicant_phone))
    if applicant_email:
        rows.append(("Email", applicant_email))
    if applicant_address:
        # Take first line for "Location" display, unless it's clearly multiline address
        loc = applicant_address.splitlines()[0].strip()
        rows.append(("Location", loc))

    label_w = right_w * 0.30
    value_w = right_w - label_w

    for label, value in rows:
        # label in subtle grey
        c.setFont(FONT_BODY, SIZE_ROLE)
        c.setFillColor(SUBTLE_GRAY)
        c.drawString(x_right, yy_right, label)

        # value in black, wrapped
        c.setFont(FONT_BODY, SIZE_ROLE)
        c.setFillColor(colors.black)
        wrapped_val = _wrap_text(c, value, value_w, FONT_BODY, SIZE_ROLE)

        # draw value at label_w offset
        val_x = x_right + label_w
        first_line = True
        for wln in wrapped_val:
            if first_line:
                c.drawString(val_x, yy_right, wln)
                first_line = False
            else:
                yy_right -= LINE
                c.drawString(val_x, yy_right, wln)

        yy_right -= LINE

    # Set y after the two-column block
    y = min(yy_left, yy_right) - 18

    # -----------------------------
    # Body
    # -----------------------------
    ensure_space(200)

    # Salutation header (bold like your template)
    salutation = f"DEAR {hiring_manager.upper()}"
    y, _ = draw_wrapped(
        salutation, margin_l, y, content_w, FONT_BOLD, SIZE_SECTION, colors.black, leading=LINE
    )
    y -= 6

    # Paragraphs (use first 3; if model gives more, we still handle but you can cap it)
    body_paras = [_clean(p) for p in paragraphs if _clean(p)]
    if not body_paras:
        body_paras = [""]  # avoid empty PDF body

    for p in body_paras[:3]:
        ensure_space(120)
        y, _ = draw_wrapped(
            p, margin_l, y, content_w, FONT_BODY, SIZE_BODY, colors.black, leading=LINE
        )
        y -= 8  # paragraph gap

    # Closing
    ensure_space(80)
    y, _ = draw_wrapped("Sincerely,", margin_l, y, content_w, FONT_BODY, SIZE_BODY)
    y -= 18  # space for signature area

    if applicant_name:
        y, _ = draw_wrapped(applicant_name, margin_l, y, content_w, FONT_BODY, SIZE_BODY)

    # Finish
    c.save()
    buf.seek(0)
    return buf.getvalue()


# -----------------------------
# Helpers
# -----------------------------
def _clean(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def _wrap_text(c: canvas.Canvas, text: str, max_width: float, font: str, size: float) -> List[str]:
    """
    Word-wrap based on ReportLab stringWidth.
    Preserves existing newlines by wrapping each line separately.
    """
    if text is None:
        return [""]

    out: List[str] = []
    for raw in str(text).splitlines():
        line = raw.strip()
        if line == "":
            out.append("")
            continue

        words = line.split()
        if not words:
            out.append("")
            continue

        current = words[0]
        for w in words[1:]:
            test = f"{current} {w}"
            if c.stringWidth(test, font, size) <= max_width:
                current = test
            else:
                out.append(current)
                current = w
        out.append(current)

    return out


def _today_string() -> str:
    return date.today().strftime("%d/%m/%Y")

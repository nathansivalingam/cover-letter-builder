from __future__ import annotations
from io import BytesIO
from typing import Any, Dict, List
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def cover_letter_text_to_pdf_bytes(data: Dict[str, Any]) -> bytes:
    """
    DICT-ONLY PDF renderer.
    Expects structured data like:
    {
      "extracted": {...},
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
    applicant_name = _clean(extracted.get("applicant_name"))
    applicant_email = _clean(extracted.get("applicant_email"))
    applicant_phone = _clean(extracted.get("applicant_phone"))
    applicant_address = _clean(extracted.get("applicant_address"))
    applicant_role = _clean(extracted.get("applicant_status_or_role"))
    company_name = _clean(extracted.get("company_name"))
    company_location = _clean(extracted.get("company_location"))
    hiring_manager = _clean(extracted.get("hiring_manager_name")) or "Hiring Manager"
    job_title = _clean(extracted.get("job_title"))
    # --- Setup canvas ---
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    left_margin = 1.0 * inch
    right_margin = 1.0 * inch
    top = height - 1.0 * inch
    bottom = 1.0 * inch
    max_width = width - left_margin - right_margin
    font_body = "Times-Roman"
    font_body_size = 12
    font_header = "Times-Bold"
    font_header_size = 12
    line_height = 14
    y = top
    def new_page():
        nonlocal y
        c.showPage()
        y = top
    def ensure_space(lines_needed: int = 1):
        nonlocal y
        if y - (lines_needed * line_height) <= bottom:
            new_page()
    def draw_wrapped(text: str, font: str = font_body, size: int = font_body_size):
        nonlocal y
        if text is None:
            return
        text = str(text)
        if text.strip() == "":
            ensure_space(1)
            y -= line_height
            return
        c.setFont(font, size)
        for line in _wrap_text(c, text, max_width, font, size):
            ensure_space(1)
            c.setFont(font, size)
            c.drawString(left_margin, y, line)
            y -= line_height
    # --- Header block (applicant) ---
    header_lines: List[str] = []
    if applicant_name:
        header_lines.append(applicant_name)
    if applicant_role:
        header_lines.append(applicant_role)
    if applicant_address:
        # preserve multi-line addresses
        for ln in applicant_address.splitlines():
            if ln.strip():
                header_lines.append(ln.strip())
    contact_bits = " | ".join([x for x in [applicant_email, applicant_phone] if x])
    if contact_bits:
        header_lines.append(contact_bits)
    # Draw header
    if header_lines:
        # name in bold if we have it
        if applicant_name:
            draw_wrapped(applicant_name, font=font_header, size=font_header_size)
            for ln in header_lines[1:]:
                draw_wrapped(ln, font=font_body, size=font_body_size)
        else:
            for ln in header_lines:
                draw_wrapped(ln, font=font_body, size=font_body_size)
        # small gap
        y -= int(line_height * 0.5)
    # Date line
    draw_wrapped(_today_string(), font=font_body, size=font_body_size)
    y -= int(line_height * 0.5)
    # --- Recipient block ---
    recipient_lines: List[str] = []
    if hiring_manager:
        recipient_lines.append(hiring_manager)
    if company_name:
        recipient_lines.append(company_name)
    if company_location:
        recipient_lines.append(company_location)
    if job_title:
        recipient_lines.append(job_title)
    for ln in recipient_lines:
        draw_wrapped(ln, font=font_body, size=font_body_size)
    # gap before body
    y -= line_height
    # --- Body ---
    draw_wrapped(f"Dear {hiring_manager},", font=font_body, size=font_body_size)
    y -= line_height  # blank line after salutation
    # paragraphs (up to 3)
    for p in paragraphs[:3]:
        p = _clean(p)
        if p:
            draw_wrapped(p, font=font_body, size=font_body_size)
            y -= line_height  # blank line after paragraph
    # Sign-off
    draw_wrapped("Kind regards,", font=font_body, size=font_body_size)
    y -= line_height  # blank line for signature
    draw_wrapped(applicant_name or "", font=font_body, size=font_body_size)
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def _clean(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()

def _wrap_text(c, text: str, max_width: float, font: str, size: int) -> List[str]:
    # word wrap based on canvas string width
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for w in words[1:]:
        test = f"{current} {w}"
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines

def _today_string() -> str:
    from datetime import date
    return date.today().strftime("%d %B %Y")

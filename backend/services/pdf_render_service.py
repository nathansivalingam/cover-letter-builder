from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def cover_letter_text_to_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER
    left_margin = 1 * inch
    right_margin = 1 * inch
    top = height - 1 * inch
    bottom = 1 * inch
    max_width = width - left_margin - right_margin

    # Basic font
    c.setFont("Times-Roman", 12)

    y = top
    line_height = 14

    def wrap_line(line: str) -> list[str]:
        # Simple word-wrap based on canvas string width
        words = line.split()
        if not words:
            return [""]

        lines = []
        current = words[0]
        for w in words[1:]:
            test = current + " " + w
            if c.stringWidth(test, "Times-Roman", 12) <= max_width:
                current = test
            else:
                lines.append(current)
                current = w
        lines.append(current)
        return lines

    for raw_line in text.splitlines():
        for line in wrap_line(raw_line):
            if y <= bottom:
                c.showPage()
                c.setFont("Times-Roman", 12)
                y = top
            c.drawString(left_margin, y, line)
            y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

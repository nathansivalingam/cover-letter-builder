from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from services.pdf_service import pdf_bytes_to_text
from services.llm_service import generate_cover_letter
from services.pdf_render_classic import render_classic_pdf
from services.pdf_render_minimal import render_minimal_pdf

router = APIRouter()


@router.post("/cover-letter")
async def cover_letter(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    output: str = Form("text"),      # "text" | "pdf"
    template: str = Form("classic"), # "classic" | "minimal"
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF")

    pdf_bytes = await resume.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    resume_text = pdf_bytes_to_text(pdf_bytes)
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    # LLM returns dict (structured)
    cover_result = generate_cover_letter(resume_text, job_description)

    if output == "pdf":
        t = (template or "classic").lower().strip()

        if t == "minimal":
            out_pdf = render_minimal_pdf(cover_result)
            filename = "cover_letter_minimal.pdf"
        else:
            out_pdf = render_classic_pdf(cover_result)
            filename = "cover_letter_classic.pdf"

        return Response(
            content=out_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # For "text" output, return the dict so frontend can use extracted fields + paragraphs
    return cover_result

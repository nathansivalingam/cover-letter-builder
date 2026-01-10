from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from services.pdf_service import pdf_bytes_to_text
from services.llm_service import generate_cover_letter
from services.pdf_render_service import cover_letter_text_to_pdf_bytes

router = APIRouter()

@router.post("/cover-letter")
async def cover_letter(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    output: str = Form("text"),  # "text" or "pdf"
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF")

    pdf_bytes = await resume.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    resume_text = pdf_bytes_to_text(pdf_bytes)
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    cover_text = generate_cover_letter(resume_text, job_description)

    if output == "pdf":
        out_pdf = cover_letter_text_to_pdf_bytes(cover_text)
        return Response(
            content=out_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cover_letter.pdf"},
        )

    return {"coverLetter": cover_text}

import json
import os
from openai import OpenAI

def _get_client() -> OpenAI:
    """
    Create the OpenAI client lazily (not at import time) so the app can boot
    even when the env isn't loaded yet (e.g. uvicorn --reload).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to backend/.env or export it in your shell."
        )
    return OpenAI(api_key=api_key)

def generate_cover_letter(resume_text: str, job_description: str) -> dict:
    client = _get_client()

    system_prompt = """
You extract structured information and write a cover letter.
Rules:
- Use ONLY the provided resume and job description.
- NEVER invent names, emails, phone numbers, addresses, hiring manager names, or company locations.
- If information is missing, return null.
- Write in Australian English.
- Cover letter must be exactly 3 paragraphs.
- Output MUST be valid JSON matching the schema exactly.
- Name MUST be a first name and a last name.
- Cover letter MUST fit on one page.
- All text MUST fall within the page margins.
- Do NOT ever include em-dashes.

"""

    user_prompt = f"""
RESUME:
{resume_text}
JOB DESCRIPTION:
{job_description}
Return JSON exactly like:
{{
  "extracted": {{
    "applicant_name": null,
    "applicant_email": null,
    "applicant_phone": null,
    "applicant_address": null,
    "applicant_status_or_role": null,
    "company_name": null,
    "company_location": null,
    "hiring_manager_name": null,
    "job_title": null
  }},
  "cover_letter": {{
    "paragraphs": ["", "", ""]
  }},
  "missing_info_questions": []
}}
"""

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
    )

    content = (resp.choices[0].message.content or "{}").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"Model returned invalid JSON:\n{content}")

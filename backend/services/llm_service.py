import json
from openai import OpenAI
client = OpenAI()

def generate_cover_letter(resume_text: str, job_description: str) -> dict:
    system_prompt = """
You extract structured information and write a cover letter.
Rules:
- Use ONLY the provided resume and job description.
- NEVER invent names, emails, phone numbers, addresses, hiring manager names, or company locations.
- If information is missing, return null.
- Write in Australian English.
- Cover letter must be exactly 3 paragraphs.
- Output MUST be valid JSON matching the schema exactly.
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
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fail loudly so you notice formatting issues early
        raise RuntimeError(f"Model returned invalid JSON:\n{content}")

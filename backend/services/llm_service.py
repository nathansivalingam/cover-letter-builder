def generate_cover_letter(resume_text: str, job_description: str) -> str:
    # TEMP: simple deterministic output so you can confirm your endpoint works.
    # Replace this later with an OpenAI call.

    resume_preview = resume_text[:800].strip()
    job_preview = job_description[:800].strip()

    return (
        "Dear Hiring Manager,\n\n"
        "I’m writing to apply for this role. Based on my background and the job requirements, "
        "I’m confident I can contribute quickly and effectively.\n\n"
        "Resume highlights (preview):\n"
        f"{resume_preview}\n\n"
        "Job description (preview):\n"
        f"{job_preview}\n\n"
        "I’d welcome the opportunity to discuss how my skills align with your needs.\n\n"
        "Kind regards,\n"
        "Nathan\n"
    )

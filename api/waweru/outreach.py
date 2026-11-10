from google import genai
from google.genai import types

from api.dad.job import JobApplied
from api.dad.outreach import OutreachContact
from api.warren.config import Settings
from api.waweru.prompt import SYSTEM_PROMPT


def draft_outreach_email(job: JobApplied, contact: OutreachContact) -> tuple[str, str]:
    settings = Settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""
Draft an outreach email to {contact.first_name} {contact.last_name}, who is {contact.position or "a hiring contact"} at {job.company}.

Elaine has applied for or is interested in: {job.job_title} at {job.company} ({job.location or "location not specified"}).

Write the subject line and email body. Format your response exactly as:
SUBJECT: <subject line>
BODY:
<email body>
""".strip()

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    text = response.text.strip()
    subject = ""
    body = ""
    if "SUBJECT:" in text and "BODY:" in text:
        parts = text.split("BODY:", 1)
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
    else:
        subject = f"A conversation worth having — {job.job_title} at {job.company}"
        body = text

    return subject, body

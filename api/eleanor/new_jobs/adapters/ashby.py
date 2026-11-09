from datetime import date
from typing import List

import requests

from api.eleanor.new_jobs.base import (
    JobAdapter,
    JobAppliedCreate,
    passes_date_filter,
    passes_description_filter,
    passes_title_filter,
)

ASHBY_SLUGS = [
    "linear",
    "notion",
    "vercel",
    "supabase",
    "clerk",
]


class AshbyAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        jobs: List[JobAppliedCreate] = []
        for slug in ASHBY_SLUGS:
            try:
                resp = requests.get(
                    f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for item in data.get("jobPostings", []):
                    title = item.get("title", "")
                    if not passes_title_filter(title):
                        continue

                    posted_date = None
                    published = item.get("publishedDate")
                    if published:
                        try:
                            posted_date = date.fromisoformat(published[:10])
                        except ValueError:
                            pass

                    if not passes_date_filter(posted_date):
                        continue

                    description = item.get("descriptionPlain", "")
                    if not passes_description_filter(description):
                        continue

                    jobs.append(
                        JobAppliedCreate(
                            company=slug.title(),
                            job_title=title,
                            location=item.get("location"),
                            job_url=item.get("applyUrl") or item.get("jobUrl"),
                            posted_date=posted_date,
                            description=description,
                            source="ashby",
                        )
                    )
            except Exception:
                continue
        return jobs

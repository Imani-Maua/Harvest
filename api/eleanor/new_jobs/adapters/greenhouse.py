from datetime import datetime, timezone
from typing import List

import requests

from api.eleanor.new_jobs.base import (
    JobAdapter,
    JobAppliedCreate,
    passes_date_filter,
    passes_description_filter,
    passes_title_filter,
)

GREENHOUSE_SLUGS = [
    "monzo",
    "revolut",
    "deliveroo",
    "bumble",
    "babylon",
    "tiktok",
    "stripe",
]


class GreenhouseAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        jobs: List[JobAppliedCreate] = []
        for slug in GREENHOUSE_SLUGS:
            try:
                resp = requests.get(
                    f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    if not passes_title_filter(title):
                        continue

                    posted_date = None
                    updated_at = item.get("updated_at")
                    if updated_at:
                        try:
                            posted_date = datetime.fromisoformat(
                                updated_at.replace("Z", "+00:00")
                            ).date()
                        except ValueError:
                            pass

                    if not passes_date_filter(posted_date):
                        continue

                    location = None
                    loc = item.get("location")
                    if isinstance(loc, dict):
                        location = loc.get("name")
                    elif isinstance(loc, str):
                        location = loc

                    jobs.append(
                        JobAppliedCreate(
                            company=slug.title(),
                            job_title=title,
                            location=location,
                            job_url=item.get("absolute_url"),
                            posted_date=posted_date,
                            source="greenhouse",
                        )
                    )
            except Exception:
                continue
        return jobs

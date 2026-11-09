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

LEVER_SLUGS = [
    "monzo",
    "revolut",
    "wise",
    "typeform",
    "hotjar",
]


class LeverAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        jobs: List[JobAppliedCreate] = []
        for slug in LEVER_SLUGS:
            try:
                resp = requests.get(
                    f"https://api.lever.co/v0/postings/{slug}?mode=json",
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue
                for item in resp.json():
                    title = item.get("text", "")
                    if not passes_title_filter(title):
                        continue

                    posted_date = None
                    created_at = item.get("createdAt")
                    if created_at:
                        try:
                            posted_date = datetime.fromtimestamp(
                                created_at / 1000, tz=timezone.utc
                            ).date()
                        except (ValueError, OSError):
                            pass

                    if not passes_date_filter(posted_date):
                        continue

                    description = item.get("descriptionPlain", "")
                    if not passes_description_filter(description):
                        continue

                    categories = item.get("categories", {})
                    location = categories.get("location") or categories.get("allLocations", [None])[0]

                    jobs.append(
                        JobAppliedCreate(
                            company=slug.title(),
                            job_title=title,
                            location=location,
                            job_url=item.get("hostedUrl"),
                            posted_date=posted_date,
                            description=description,
                            source="lever",
                        )
                    )
            except Exception:
                continue
        return jobs

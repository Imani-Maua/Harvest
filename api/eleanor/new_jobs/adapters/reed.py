from datetime import datetime
from typing import List

import requests
from sqlalchemy.orm import Session

from api.dad.candidate import CareerPreference
from api.warren.config import Settings
from api.eleanor.new_jobs.base import (
    JobAdapter,
    JobAppliedCreate,
    passes_date_filter,
    passes_description_filter,
    passes_title_filter,
)

settings = Settings()

DEFAULT_QUERIES = ["software engineer", "backend engineer", "python developer"]
DEFAULT_LOCATIONS = ["London"]
RESULTS_TO_TAKE = 50


class ReedAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        if not settings.REED_API_KEY:
            return []

        db: Session | None = kwargs.get("db")
        queries, locations = _get_search_terms(db)

        jobs: List[JobAppliedCreate] = []
        seen_ids: set[int] = set()

        for query in queries:
            for location in locations:
                try:
                    resp = requests.get(
                        "https://www.reed.co.uk/api/1.0/search",
                        params={
                            "keywords": query,
                            "locationName": location,
                            "resultsToTake": RESULTS_TO_TAKE,
                        },
                        auth=(settings.REED_API_KEY, ""),
                        timeout=15,
                    )
                    if resp.status_code != 200:
                        continue
                    for item in resp.json().get("results", []):
                        job_id = item.get("jobId")
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        title = item.get("jobTitle", "")
                        if not passes_title_filter(title):
                            continue

                        posted_date = None
                        date_str = item.get("date")
                        if date_str:
                            for fmt in ("%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
                                try:
                                    posted_date = datetime.strptime(date_str, fmt).date()
                                    break
                                except ValueError:
                                    pass

                        if not passes_date_filter(posted_date):
                            continue

                        description = item.get("jobDescription", "")
                        if not passes_description_filter(description):
                            continue

                        jobs.append(
                            JobAppliedCreate(
                                company=item.get("employerName", "Unknown"),
                                job_title=title,
                                location=item.get("locationName"),
                                job_url=item.get("jobUrl"),
                                posted_date=posted_date,
                                description=description,
                                source="reed",
                            )
                        )
                except Exception:
                    continue

        return jobs


def _get_search_terms(db: Session | None) -> tuple[list[str], list[str]]:
    if not db:
        return DEFAULT_QUERIES, DEFAULT_LOCATIONS

    pref = db.query(CareerPreference).first()
    if not pref:
        return DEFAULT_QUERIES, DEFAULT_LOCATIONS

    queries = pref.desired_titles or DEFAULT_QUERIES
    locations = pref.desired_locations or DEFAULT_LOCATIONS
    return queries, locations

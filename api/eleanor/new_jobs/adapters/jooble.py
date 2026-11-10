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


class JoobleAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        if not settings.JOOBLE_API_KEY:
            return []

        db: Session | None = kwargs.get("db")
        queries, locations = _get_search_terms(db)

        jobs: List[JobAppliedCreate] = []
        seen_urls: set[str] = set()

        for query in queries:
            for location in locations:
                try:
                    resp = requests.post(
                        f"https://jooble.org/api/{settings.JOOBLE_API_KEY}",
                        json={"keywords": query, "location": location, "page": 1},
                        timeout=15,
                    )
                    if resp.status_code != 200:
                        continue
                    for item in resp.json().get("jobs", []):
                        link = item.get("link", "")
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)

                        title = item.get("title", "")
                        if not passes_title_filter(title):
                            continue

                        posted_date = None
                        updated = item.get("updated")
                        if updated:
                            try:
                                posted_date = datetime.fromisoformat(updated).date()
                            except ValueError:
                                pass

                        if not passes_date_filter(posted_date):
                            continue

                        description = item.get("snippet", "")
                        if not passes_description_filter(description):
                            continue

                        jobs.append(
                            JobAppliedCreate(
                                company=item.get("company", "Unknown"),
                                job_title=title,
                                location=item.get("location"),
                                job_url=link or None,
                                posted_date=posted_date,
                                description=description,
                                source="jooble",
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

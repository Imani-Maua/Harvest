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
DEFAULT_LOCATIONS = ["London", "United Kingdom"]
COUNTRY = "gb"
RESULTS_PER_PAGE = 50


class AdzunaAdapter(JobAdapter):
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
            return []

        db: Session | None = kwargs.get("db")
        queries, locations = _get_search_terms(db)

        jobs: List[JobAppliedCreate] = []
        seen_ids: set[str] = set()

        for query in queries:
            for location in locations:
                try:
                    resp = requests.get(
                        f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1",
                        params={
                            "app_id": settings.ADZUNA_APP_ID,
                            "app_key": settings.ADZUNA_APP_KEY,
                            "what": query,
                            "where": location,
                            "results_per_page": RESULTS_PER_PAGE,
                            "content-type": "application/json",
                        },
                        timeout=15,
                    )
                    if resp.status_code != 200:
                        continue
                    for item in resp.json().get("results", []):
                        item_id = str(item.get("id", ""))
                        if item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        title = item.get("title", "")
                        if not passes_title_filter(title):
                            continue

                        posted_date = None
                        created = item.get("created")
                        if created:
                            try:
                                posted_date = datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                ).date()
                            except ValueError:
                                pass

                        if not passes_date_filter(posted_date):
                            continue

                        description = item.get("description", "")
                        if not passes_description_filter(description):
                            continue

                        company_data = item.get("company", {})
                        company = company_data.get("display_name", "Unknown") if isinstance(company_data, dict) else "Unknown"

                        loc_data = item.get("location", {})
                        loc_str = loc_data.get("display_name") if isinstance(loc_data, dict) else None

                        jobs.append(
                            JobAppliedCreate(
                                company=company,
                                job_title=title,
                                location=loc_str,
                                job_url=item.get("redirect_url"),
                                posted_date=posted_date,
                                description=description,
                                source="adzuna",
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

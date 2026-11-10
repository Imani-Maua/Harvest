"""End-to-end tests for run_ingestion()."""
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest

from api.dad.enums import SponsorshipStatus
from api.eleanor.new_jobs.base import JobAppliedCreate
from api.eleanor.new_jobs.ingestion import run_ingestion

Row = namedtuple("Row", ["job_url", "company", "job_title"])

SPONSORS_PATCH = "api.eleanor.new_jobs.ingestion.download_uk_sponsors"
ADAPTERS_PATCH = "api.eleanor.new_jobs.ingestion.ADAPTERS"


def make_job(company="Monzo", title="Software Engineer", url="https://url/1", description=""):
    return JobAppliedCreate(
        company=company, job_title=title, job_url=url, description=description
    )


def make_adapter(name="MockAdapter", jobs=None, error=None):
    """Return a mock adapter class whose .fetch() returns `jobs` or raises `error`."""
    cls = MagicMock()
    cls.__name__ = name
    if error:
        cls.return_value.fetch.side_effect = error
    else:
        cls.return_value.fetch.return_value = jobs or []
    return cls


def empty_db():
    db = MagicMock()
    db.query.return_value.all.return_value = []
    return db


class TestRunIngestion:
    def test_all_adapters_empty_returns_zero_counts(self):
        db = empty_db()
        adapters = [make_adapter(f"A{i}") for i in range(6)]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result == {"fetched": 0, "new": 0, "skipped": 0, "adapter_errors": {}}

    def test_new_job_saved_to_db(self):
        db = empty_db()
        job = make_job("Monzo", "Junior Software Engineer", "https://monzo.com/1")
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result["fetched"] == 1
        assert result["new"] == 1
        assert result["skipped"] == 0
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_duplicate_url_in_db_not_saved(self):
        existing = [Row("https://monzo.com/1", "Monzo", "Junior Software Engineer")]
        db = MagicMock()
        db.query.return_value.all.return_value = existing

        job = make_job("Monzo", "Junior Software Engineer", "https://monzo.com/1")
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result["new"] == 0
        assert result["skipped"] == 1
        db.add.assert_not_called()

    def test_adapter_exception_captured_in_errors(self):
        db = empty_db()
        broken = make_adapter("GreenhouseAdapter", error=RuntimeError("API rate limit hit"))
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, [broken]):
            result = run_ingestion(db)
        assert "GreenhouseAdapter" in result["adapter_errors"]
        assert "rate limit" in result["adapter_errors"]["GreenhouseAdapter"]
        assert result["fetched"] == 0

    def test_one_adapter_error_others_still_run(self):
        db = empty_db()
        good_job = make_job("Revolut", "Python Developer", "https://revolut.com/1")
        adapters = [
            make_adapter("BrokenAdapter", error=RuntimeError("boom")),
            make_adapter("GoodAdapter", jobs=[good_job]),
        ]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result["new"] == 1
        assert "BrokenAdapter" in result["adapter_errors"]

    def test_sponsorship_confirmed_for_register_company(self):
        db = empty_db()
        register = {"monzo bank limited"}
        job = make_job("Monzo Bank Limited", "Junior SE", "https://url/2", "")
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=register), \
             patch(ADAPTERS_PATCH, adapters):
            run_ingestion(db)
        added = db.add.call_args[0][0]
        assert added.sponsorship_status == SponsorshipStatus.confirmed

    def test_sponsorship_no_info_for_unknown_company(self):
        db = empty_db()
        job = make_job("Unknown Startup", "Software Engineer", "https://url/3",
                       "Great role for a passionate engineer. Competitive salary.")
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            run_ingestion(db)
        added = db.add.call_args[0][0]
        assert added.sponsorship_status == SponsorshipStatus.no_info

    def test_sponsorship_explicitly_unavailable(self):
        db = empty_db()
        job = make_job("Corp", "Python Developer", "https://url/4",
                       "Great role. We are unable to sponsor visas at this time.")
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            run_ingestion(db)
        added = db.add.call_args[0][0]
        assert added.sponsorship_status == SponsorshipStatus.explicitly_unavailable

    def test_all_job_fields_populated_on_saved_object(self):
        db = empty_db()
        from datetime import date
        job = JobAppliedCreate(
            company="Stripe",
            job_title="Software Engineer",
            job_url="https://stripe.com/jobs/1",
            location="London",
            source="greenhouse",
            posted_date=date.today(),
            description="Build payment systems.",
        )
        adapters = [make_adapter("Greenhouse", jobs=[job])]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            run_ingestion(db)
        added = db.add.call_args[0][0]
        assert added.company == "Stripe"
        assert added.location == "London"
        assert added.source == "greenhouse"
        assert added.description == "Build payment systems."
        assert added.sponsorship_evidence is not None

    def test_multiple_jobs_multiple_add_calls(self):
        db = empty_db()
        jobs = [
            make_job("Alpha", "Python Dev", "https://alpha.com/1"),
            make_job("Beta", "Backend Eng", "https://beta.com/1"),
        ]
        adapters = [make_adapter("Greenhouse", jobs=jobs)]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result["new"] == 2
        assert db.add.call_count == 2
        db.commit.assert_called_once()

    def test_fetched_count_includes_filtered_duplicates(self):
        """fetched = all jobs before dedup; skipped = fetched - new."""
        existing = [Row("https://old.com/1", "OldCorp", "SE")]
        db = MagicMock()
        db.query.return_value.all.return_value = existing
        jobs = [
            make_job("OldCorp", "SE", "https://old.com/1"),   # duplicate → skipped
            make_job("NewCorp", "BE", "https://new.com/1"),   # new
        ]
        adapters = [make_adapter("Greenhouse", jobs=jobs)]
        with patch(SPONSORS_PATCH, return_value=set()), \
             patch(ADAPTERS_PATCH, adapters):
            result = run_ingestion(db)
        assert result["fetched"] == 2
        assert result["new"] == 1
        assert result["skipped"] == 1

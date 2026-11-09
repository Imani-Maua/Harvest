"""Tests for api/eleanor/new_jobs/dedup.py."""
from collections import namedtuple
from unittest.mock import MagicMock

import pytest

from api.eleanor.new_jobs.base import JobAppliedCreate
from api.eleanor.new_jobs.dedup import deduplicate

Row = namedtuple("Row", ["job_url", "company", "job_title"])


def make_job(company="Acme", title="Software Engineer", url=None):
    return JobAppliedCreate(company=company, job_title=title, job_url=url)


def mock_db_with(rows):
    db = MagicMock()
    db.query.return_value.all.return_value = rows
    return db


class TestDeduplicateAgainstExisting:
    def test_empty_existing_all_pass(self):
        db = mock_db_with([])
        jobs = [make_job("Alpha", "Software Engineer", "https://jobs.alpha.com/1")]
        assert len(deduplicate(jobs, db)) == 1

    def test_url_match_existing_skipped(self):
        existing = [Row("https://jobs.alpha.com/1", "Alpha", "Software Engineer")]
        db = mock_db_with(existing)
        jobs = [make_job("Alpha", "Software Engineer", "https://jobs.alpha.com/1")]
        assert deduplicate(jobs, db) == []

    def test_url_trailing_slash_normalised(self):
        existing = [Row("https://jobs.alpha.com/1/", "Alpha", "SE")]
        db = mock_db_with(existing)
        jobs = [make_job("Alpha", "SE", "https://jobs.alpha.com/1")]
        assert deduplicate(jobs, db) == []

    def test_url_query_params_stripped(self):
        existing = [Row("https://jobs.alpha.com/1", "Alpha", "SE")]
        db = mock_db_with(existing)
        jobs = [make_job("Alpha", "SE", "https://jobs.alpha.com/1?ref=linkedin&src=job")]
        assert deduplicate(jobs, db) == []

    def test_url_case_normalised(self):
        existing = [Row("https://jobs.alpha.com/1", "Alpha", "SE")]
        db = mock_db_with(existing)
        jobs = [make_job("Alpha", "SE", "HTTPS://JOBS.ALPHA.COM/1")]
        assert deduplicate(jobs, db) == []

    def test_fuzzy_company_title_match_skipped(self):
        # Identical company and title → fuzzy match at 100% → skipped
        existing = [Row(None, "DeepMind", "Graduate Software Engineer")]
        db = mock_db_with(existing)
        jobs = [make_job("DeepMind", "Graduate Software Engineer")]
        assert deduplicate(jobs, db) == []

    def test_slightly_different_company_passes(self):
        # "GoogleDeepMind" vs "DeepMind" → low similarity → passes
        existing = [Row(None, "DeepMind", "Software Engineer")]
        db = mock_db_with(existing)
        jobs = [make_job("GoogleDeepMind", "Software Engineer")]
        result = deduplicate(jobs, db)
        assert len(result) == 1

    def test_different_title_same_company_passes(self):
        existing = [Row(None, "Monzo", "Backend Engineer")]
        db = mock_db_with(existing)
        jobs = [make_job("Monzo", "Frontend Engineer")]
        result = deduplicate(jobs, db)
        assert len(result) == 1

    def test_multiple_existing_one_match_skipped(self):
        existing = [
            Row("https://a.com/1", "Alpha", "SE"),
            Row("https://b.com/2", "Beta", "BE"),
        ]
        db = mock_db_with(existing)
        jobs = [
            make_job("Alpha", "SE", "https://a.com/1"),   # skipped
            make_job("Gamma", "FE", "https://c.com/3"),   # new
        ]
        result = deduplicate(jobs, db)
        assert len(result) == 1
        assert result[0].company == "Gamma"


class TestDeduplicateWithinBatch:
    def test_duplicate_url_in_batch_second_skipped(self):
        db = mock_db_with([])
        url = "https://jobs.company.com/42"
        jobs = [
            make_job("Company", "Software Engineer", url),
            make_job("Company", "Software Engineer", url),
        ]
        assert len(deduplicate(jobs, db)) == 1

    def test_fuzzy_duplicate_no_url_second_skipped(self):
        db = mock_db_with([])
        jobs = [
            make_job("Monzo", "Junior Software Engineer"),
            make_job("Monzo", "Junior Software Engineer"),
        ]
        assert len(deduplicate(jobs, db)) == 1

    def test_different_jobs_all_pass(self):
        db = mock_db_with([])
        jobs = [
            make_job("Monzo", "Backend Engineer", "https://monzo.com/1"),
            make_job("Revolut", "Frontend Engineer", "https://revolut.com/2"),
            make_job("Wise", "Python Developer", "https://wise.com/3"),
        ]
        assert len(deduplicate(jobs, db)) == 3

    def test_no_url_no_fuzzy_match_all_pass(self):
        db = mock_db_with([])
        jobs = [
            make_job("Acme", "Software Engineer"),
            make_job("Beta Corp", "Backend Engineer"),
        ]
        assert len(deduplicate(jobs, db)) == 2

    def test_same_url_different_companies_still_deduped(self):
        # Same URL = same job regardless of company name discrepancy
        db = mock_db_with([])
        url = "https://jobs.company.com/99"
        jobs = [
            make_job("CompanyA", "SE", url),
            make_job("CompanyB", "BE", url),
        ]
        assert len(deduplicate(jobs, db)) == 1

    def test_no_url_jobs_checked_by_fuzzy(self):
        db = mock_db_with([])
        # Two no-URL jobs with the same company+title should be deduped
        jobs = [
            make_job("Stripe", "Software Engineer"),
            make_job("Stripe", "Software Engineer"),
        ]
        assert len(deduplicate(jobs, db)) == 1

    def test_order_preserved_first_wins(self):
        db = mock_db_with([])
        url = "https://jobs.company.com/1"
        j1 = make_job("Alpha", "SE", url)
        j2 = make_job("Alpha", "SE", url)
        result = deduplicate([j1, j2], db)
        assert result[0] is j1

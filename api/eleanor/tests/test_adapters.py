"""Tests for all 6 job adapters — HTTP is fully mocked."""
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from api.eleanor.new_jobs.adapters.adzuna import AdzunaAdapter
from api.eleanor.new_jobs.adapters.ashby import AshbyAdapter
from api.eleanor.new_jobs.adapters.greenhouse import GreenhouseAdapter
from api.eleanor.new_jobs.adapters.jooble import JoobleAdapter
from api.eleanor.new_jobs.adapters.lever import LeverAdapter
from api.eleanor.new_jobs.adapters.reed import ReedAdapter

TODAY = date.today()
RECENT_DATE = (TODAY - timedelta(days=5)).isoformat()
OLD_DATE = (TODAY - timedelta(days=30)).isoformat()


def make_resp(json_data, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data
    return r


# ── Greenhouse ────────────────────────────────────────────────────────────────

class TestGreenhouseAdapter:
    def test_valid_job_returned(self):
        from api.eleanor.new_jobs.adapters.greenhouse import GREENHOUSE_SLUGS
        valid_resp = make_resp({
            "jobs": [{
                "title": "Junior Software Engineer",
                "updated_at": f"{RECENT_DATE}T00:00:00Z",
                "absolute_url": "https://boards.greenhouse.io/monzo/jobs/1",
                "location": {"name": "London"},
            }]
        })
        empty_resp = make_resp({"jobs": []})
        side_effects = [valid_resp] + [empty_resp] * (len(GREENHOUSE_SLUGS) - 1)
        with patch("requests.get", side_effect=side_effects):
            jobs = GreenhouseAdapter().fetch()
        assert len(jobs) == 1
        assert jobs[0].source == "greenhouse"
        assert jobs[0].company == "Monzo"
        assert jobs[0].location == "London"

    def test_title_filter_applied(self):
        resp = make_resp({
            "jobs": [{"title": "Senior Software Engineer", "updated_at": f"{RECENT_DATE}T00:00:00Z",
                      "absolute_url": "https://url", "location": None}]
        })
        with patch("requests.get", return_value=resp):
            assert GreenhouseAdapter().fetch() == []

    def test_date_filter_applied(self):
        resp = make_resp({
            "jobs": [{"title": "Junior Software Engineer", "updated_at": f"{OLD_DATE}T00:00:00Z",
                      "absolute_url": "https://url", "location": None}]
        })
        with patch("requests.get", return_value=resp):
            assert GreenhouseAdapter().fetch() == []

    def test_non_200_response_skipped(self):
        with patch("requests.get", return_value=make_resp({}, status=404)):
            assert GreenhouseAdapter().fetch() == []

    def test_location_as_string_used_directly(self):
        resp = make_resp({
            "jobs": [{
                "title": "Graduate Software Engineer",
                "updated_at": f"{RECENT_DATE}T00:00:00Z",
                "absolute_url": "https://url",
                "location": "Remote",
            }]
        })
        with patch("requests.get", return_value=resp):
            jobs = GreenhouseAdapter().fetch()
        assert jobs[0].location == "Remote"

    def test_missing_location_is_none(self):
        resp = make_resp({
            "jobs": [{
                "title": "Graduate Software Engineer",
                "updated_at": f"{RECENT_DATE}T00:00:00Z",
                "absolute_url": "https://url",
                "location": None,
            }]
        })
        with patch("requests.get", return_value=resp):
            jobs = GreenhouseAdapter().fetch()
        assert jobs[0].location is None

    def test_network_exception_skipped(self):
        with patch("requests.get", side_effect=Exception("timeout")):
            assert GreenhouseAdapter().fetch() == []

    def test_multiple_slugs_aggregated(self):
        # Two slugs both return one valid job each
        resp = make_resp({
            "jobs": [{
                "title": "Software Engineer",
                "updated_at": f"{RECENT_DATE}T00:00:00Z",
                "absolute_url": "https://url/1",
                "location": None,
            }]
        })
        with patch("requests.get", return_value=resp):
            jobs = GreenhouseAdapter().fetch()
        # Should have one job per slug (7 slugs hardcoded)
        assert len(jobs) == 7


# ── Lever ─────────────────────────────────────────────────────────────────────

class TestLeverAdapter:
    def _recent_ms(self):
        return int((datetime.now(tz=timezone.utc) - timedelta(days=3)).timestamp() * 1000)

    def _old_ms(self):
        return int((datetime.now(tz=timezone.utc) - timedelta(days=30)).timestamp() * 1000)

    def test_valid_job_returned(self):
        from api.eleanor.new_jobs.adapters.lever import LEVER_SLUGS
        valid_resp = make_resp([{
            "text": "Backend Engineer",
            "createdAt": self._recent_ms(),
            "hostedUrl": "https://jobs.lever.co/monzo/123",
            "descriptionPlain": "Build great backend systems.",
            "categories": {"location": "London"},
        }])
        empty_resp = make_resp([])
        side_effects = [valid_resp] + [empty_resp] * (len(LEVER_SLUGS) - 1)
        with patch("requests.get", side_effect=side_effects):
            jobs = LeverAdapter().fetch()
        assert len(jobs) == 1
        assert jobs[0].source == "lever"
        assert jobs[0].location == "London"

    def test_title_filter_applied(self):
        resp = make_resp([{
            "text": "Director of Engineering",
            "createdAt": self._recent_ms(),
            "hostedUrl": "https://url",
            "descriptionPlain": "",
            "categories": {},
        }])
        with patch("requests.get", return_value=resp):
            assert LeverAdapter().fetch() == []

    def test_old_job_filtered(self):
        resp = make_resp([{
            "text": "Junior Software Engineer",
            "createdAt": self._old_ms(),
            "hostedUrl": "https://url",
            "descriptionPlain": "",
            "categories": {},
        }])
        with patch("requests.get", return_value=resp):
            assert LeverAdapter().fetch() == []

    def test_description_filter_applied(self):
        resp = make_resp([{
            "text": "Software Engineer",
            "createdAt": self._recent_ms(),
            "hostedUrl": "https://url",
            "descriptionPlain": "Requires 5+ years experience in Python.",
            "categories": {},
        }])
        with patch("requests.get", return_value=resp):
            assert LeverAdapter().fetch() == []

    def test_location_fallback_to_allLocations(self):
        resp = make_resp([{
            "text": "Python Developer",
            "createdAt": self._recent_ms(),
            "hostedUrl": "https://url",
            "descriptionPlain": "",
            "categories": {"allLocations": ["Manchester"]},
        }])
        with patch("requests.get", return_value=resp):
            jobs = LeverAdapter().fetch()
        assert jobs[0].location == "Manchester"

    def test_non_200_skipped(self):
        with patch("requests.get", return_value=make_resp([], status=403)):
            assert LeverAdapter().fetch() == []


# ── Ashby ─────────────────────────────────────────────────────────────────────

class TestAshbyAdapter:
    def test_valid_job_returned(self):
        from api.eleanor.new_jobs.adapters.ashby import ASHBY_SLUGS
        valid_resp = make_resp({
            "jobPostings": [{
                "title": "Software Engineer",
                "publishedDate": f"{RECENT_DATE}T00:00:00.000Z",
                "applyUrl": "https://jobs.ashbyhq.com/linear/abc",
                "location": "Remote",
                "descriptionPlain": "Build great software.",
            }]
        })
        empty_resp = make_resp({"jobPostings": []})
        side_effects = [valid_resp] + [empty_resp] * (len(ASHBY_SLUGS) - 1)
        with patch("requests.get", side_effect=side_effects):
            jobs = AshbyAdapter().fetch()
        assert len(jobs) == 1
        assert jobs[0].source == "ashby"
        assert jobs[0].company == "Linear"

    def test_old_posting_excluded(self):
        resp = make_resp({
            "jobPostings": [{
                "title": "Software Engineer",
                "publishedDate": f"{OLD_DATE}T00:00:00.000Z",
                "applyUrl": "https://url",
                "location": "London",
                "descriptionPlain": "",
            }]
        })
        with patch("requests.get", return_value=resp):
            assert AshbyAdapter().fetch() == []

    def test_description_filter_applied(self):
        resp = make_resp({
            "jobPostings": [{
                "title": "Software Engineer",
                "publishedDate": f"{RECENT_DATE}",
                "applyUrl": "https://url",
                "location": "London",
                "descriptionPlain": "7+ years required.",
            }]
        })
        with patch("requests.get", return_value=resp):
            assert AshbyAdapter().fetch() == []

    def test_job_url_fallback_to_job_url_field(self):
        resp = make_resp({
            "jobPostings": [{
                "title": "Python Developer",
                "publishedDate": f"{RECENT_DATE}",
                "jobUrl": "https://jobs.ashbyhq.com/notion/xyz",
                "location": "London",
                "descriptionPlain": "",
            }]
        })
        with patch("requests.get", return_value=resp):
            jobs = AshbyAdapter().fetch()
        assert jobs[0].job_url == "https://jobs.ashbyhq.com/notion/xyz"

    def test_title_filter_applied(self):
        resp = make_resp({
            "jobPostings": [{
                "title": "Staff Engineer",
                "publishedDate": f"{RECENT_DATE}",
                "applyUrl": "https://url",
                "location": "London",
                "descriptionPlain": "",
            }]
        })
        with patch("requests.get", return_value=resp):
            assert AshbyAdapter().fetch() == []


# ── Adzuna ────────────────────────────────────────────────────────────────────

class TestAdzunaAdapter:
    def test_no_keys_returns_empty(self):
        import api.eleanor.new_jobs.adapters.adzuna as mod
        with patch.object(mod, "settings") as ms:
            ms.ADZUNA_APP_ID = ""
            ms.ADZUNA_APP_KEY = ""
            assert AdzunaAdapter().fetch(db=None) == []

    def test_valid_response_parsed(self):
        import api.eleanor.new_jobs.adapters.adzuna as mod
        resp = make_resp({"results": [{
            "id": "1234",
            "title": "Junior Python Developer",
            "created": f"{RECENT_DATE}T00:00:00Z",
            "redirect_url": "https://adzuna.com/job/1234",
            "description": "Great opportunity.",
            "company": {"display_name": "Acme Ltd"},
            "location": {"display_name": "London"},
        }]})
        with patch.object(mod, "settings") as ms:
            ms.ADZUNA_APP_ID = "test_id"
            ms.ADZUNA_APP_KEY = "test_key"
            with patch("requests.get", return_value=resp):
                jobs = AdzunaAdapter().fetch(db=None)
        assert len(jobs) == 1
        assert jobs[0].source == "adzuna"
        assert jobs[0].company == "Acme Ltd"

    def test_duplicate_id_deduped(self):
        import api.eleanor.new_jobs.adapters.adzuna as mod
        item = {
            "id": "99",
            "title": "Software Engineer",
            "created": f"{RECENT_DATE}T00:00:00Z",
            "redirect_url": "https://url",
            "description": "",
            "company": {"display_name": "Corp"},
            "location": {"display_name": "London"},
        }
        resp = make_resp({"results": [item, item]})
        with patch.object(mod, "settings") as ms:
            ms.ADZUNA_APP_ID = "id"
            ms.ADZUNA_APP_KEY = "key"
            with patch("requests.get", return_value=resp):
                jobs = AdzunaAdapter().fetch(db=None)
        assert len(jobs) == 1

    def test_uses_career_preferences_from_db(self):
        import api.eleanor.new_jobs.adapters.adzuna as mod
        pref = MagicMock()
        pref.desired_titles = ["machine learning engineer"]
        pref.desired_locations = ["Manchester"]
        db = MagicMock()
        db.query.return_value.first.return_value = pref

        resp = make_resp({"results": []})
        with patch.object(mod, "settings") as ms:
            ms.ADZUNA_APP_ID = "id"
            ms.ADZUNA_APP_KEY = "key"
            with patch("requests.get", return_value=resp) as mock_get:
                AdzunaAdapter().fetch(db=db)
                call_kwargs = mock_get.call_args[1]["params"]
                assert call_kwargs["what"] == "machine learning engineer"
                assert call_kwargs["where"] == "Manchester"

    def test_no_db_uses_defaults(self):
        import api.eleanor.new_jobs.adapters.adzuna as mod
        resp = make_resp({"results": []})
        with patch.object(mod, "settings") as ms:
            ms.ADZUNA_APP_ID = "id"
            ms.ADZUNA_APP_KEY = "key"
            with patch("requests.get", return_value=resp) as mock_get:
                AdzunaAdapter().fetch(db=None)
                call_kwargs = mock_get.call_args[1]["params"]
                # Default queries from DEFAULT_QUERIES
                assert call_kwargs["what"] in ["software engineer", "backend engineer", "python developer"]


# ── Reed ──────────────────────────────────────────────────────────────────────

class TestReedAdapter:
    def test_no_key_returns_empty(self):
        import api.eleanor.new_jobs.adapters.reed as mod
        with patch.object(mod, "settings") as ms:
            ms.REED_API_KEY = ""
            assert ReedAdapter().fetch(db=None) == []

    def test_valid_response_parsed(self):
        import api.eleanor.new_jobs.adapters.reed as mod
        resp = make_resp({"results": [{
            "jobId": 1,
            "jobTitle": "Graduate Software Engineer",
            "date": TODAY.strftime("%d/%m/%Y"),
            "jobUrl": "https://reed.co.uk/job/1",
            "jobDescription": "Entry level role.",
            "employerName": "TechCorp",
            "locationName": "London",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.REED_API_KEY = "test_key"
            with patch("requests.get", return_value=resp):
                jobs = ReedAdapter().fetch(db=None)
        assert len(jobs) == 1
        assert jobs[0].source == "reed"
        assert jobs[0].company == "TechCorp"

    def test_duplicate_job_id_deduped(self):
        import api.eleanor.new_jobs.adapters.reed as mod
        item = {
            "jobId": 42,
            "jobTitle": "Junior Software Engineer",
            "date": TODAY.strftime("%d/%m/%Y"),
            "jobUrl": "https://reed.co.uk/job/42",
            "jobDescription": "",
            "employerName": "Corp",
            "locationName": "London",
        }
        resp = make_resp({"results": [item, item]})
        with patch.object(mod, "settings") as ms:
            ms.REED_API_KEY = "test_key"
            with patch("requests.get", return_value=resp):
                jobs = ReedAdapter().fetch(db=None)
        assert len(jobs) == 1

    def test_old_date_filtered(self):
        import api.eleanor.new_jobs.adapters.reed as mod
        resp = make_resp({"results": [{
            "jobId": 2,
            "jobTitle": "Software Engineer",
            "date": (TODAY - timedelta(days=30)).strftime("%d/%m/%Y"),
            "jobUrl": "https://reed.co.uk/job/2",
            "jobDescription": "",
            "employerName": "Corp",
            "locationName": "London",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.REED_API_KEY = "test_key"
            with patch("requests.get", return_value=resp):
                assert ReedAdapter().fetch(db=None) == []

    def test_description_filter_applied(self):
        import api.eleanor.new_jobs.adapters.reed as mod
        resp = make_resp({"results": [{
            "jobId": 3,
            "jobTitle": "Software Engineer",
            "date": TODAY.strftime("%d/%m/%Y"),
            "jobUrl": "https://url",
            "jobDescription": "10+ years experience required.",
            "employerName": "Corp",
            "locationName": "London",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.REED_API_KEY = "test_key"
            with patch("requests.get", return_value=resp):
                assert ReedAdapter().fetch(db=None) == []


# ── Jooble ────────────────────────────────────────────────────────────────────

class TestJoobleAdapter:
    def test_no_key_returns_empty(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = ""
            assert JoobleAdapter().fetch(db=None) == []

    def test_valid_response_parsed(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        resp = make_resp({"jobs": [{
            "title": "Python Developer",
            "link": "https://jooble.org/jd/1",
            "updated": f"{RECENT_DATE}T10:00:00",
            "snippet": "Looking for entry level Python dev.",
            "company": "DevCo",
            "location": "London, UK",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = "test_key"
            with patch("requests.post", return_value=resp):
                jobs = JoobleAdapter().fetch(db=None)
        assert len(jobs) == 1
        assert jobs[0].source == "jooble"
        assert jobs[0].company == "DevCo"

    def test_duplicate_link_deduped(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        item = {
            "title": "Software Engineer",
            "link": "https://jooble.org/jd/99",
            "updated": f"{RECENT_DATE}T10:00:00",
            "snippet": "",
            "company": "Corp",
            "location": "London",
        }
        resp = make_resp({"jobs": [item, item]})
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = "test_key"
            with patch("requests.post", return_value=resp):
                jobs = JoobleAdapter().fetch(db=None)
        assert len(jobs) == 1

    def test_old_job_filtered(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        resp = make_resp({"jobs": [{
            "title": "Software Engineer",
            "link": "https://jooble.org/jd/2",
            "updated": f"{OLD_DATE}T10:00:00",
            "snippet": "",
            "company": "Corp",
            "location": "London",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = "test_key"
            with patch("requests.post", return_value=resp):
                assert JoobleAdapter().fetch(db=None) == []

    def test_non_200_skipped(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = "test_key"
            with patch("requests.post", return_value=make_resp({}, status=500)):
                assert JoobleAdapter().fetch(db=None) == []

    def test_empty_link_becomes_none(self):
        import api.eleanor.new_jobs.adapters.jooble as mod
        resp = make_resp({"jobs": [{
            "title": "Python Developer",
            "link": "",
            "updated": f"{RECENT_DATE}T10:00:00",
            "snippet": "Good role.",
            "company": "Corp",
            "location": "London",
        }]})
        with patch.object(mod, "settings") as ms:
            ms.JOOBLE_API_KEY = "test_key"
            with patch("requests.post", return_value=resp):
                jobs = JoobleAdapter().fetch(db=None)
        assert jobs[0].job_url is None

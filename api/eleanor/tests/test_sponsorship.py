"""Tests for api/eleanor/new_jobs/sponsorship.py."""
from unittest.mock import MagicMock, patch

import pytest

from api.dad.enums import SponsorshipStatus
from api.eleanor.new_jobs.sponsorship import classify_sponsorship, download_uk_sponsors

REGISTER = {"monzo bank limited", "revolut ltd", "stripe inc"}

CSV_CONTENT = (
    "Organisation Name,Town/City,County,Type & Rating\n"
    "Monzo Bank Limited,London,Greater London,Worker-Skilled\n"
    "Revolut Ltd,London,Greater London,Worker-Skilled\n"
)
CSV_URL = "https://assets.publishing.service.gov.uk/Worker_and_Temporary_Worker_2024.csv"


def _make_page_resp(csv_url=CSV_URL):
    r = MagicMock()
    r.status_code = 200
    r.text = f'<a href="{csv_url}">file</a>'
    r.raise_for_status = MagicMock()
    return r


def _make_csv_resp(content=CSV_CONTENT):
    r = MagicMock()
    r.status_code = 200
    r.text = content
    r.raise_for_status = MagicMock()
    return r


class TestClassifySponsorship:
    def test_exact_register_match_confirmed(self):
        status, evidence = classify_sponsorship("Monzo Bank Limited", "", REGISTER)
        assert status == SponsorshipStatus.confirmed
        assert "sponsor register" in evidence.lower()

    def test_fuzzy_register_match_confirmed(self):
        # Single-char typo → still above 85% threshold
        status, _ = classify_sponsorship("Monzo Bank Limted", "", REGISTER)
        assert status == SponsorshipStatus.confirmed

    def test_case_insensitive_register_match(self):
        status, _ = classify_sponsorship("MONZO BANK LIMITED", "", REGISTER)
        assert status == SponsorshipStatus.confirmed

    def test_no_sponsorship_phrase_explicitly_unavailable(self):
        status, evidence = classify_sponsorship(
            "Unknown Corp", "We are unable to sponsor visas at this time.", set()
        )
        assert status == SponsorshipStatus.explicitly_unavailable
        assert "unable to sponsor" in evidence.lower()

    def test_no_visa_sponsorship_phrase(self):
        status, _ = classify_sponsorship("Corp", "No visa sponsorship provided.", set())
        assert status == SponsorshipStatus.explicitly_unavailable

    def test_cannot_sponsor_phrase(self):
        status, _ = classify_sponsorship("Corp", "We cannot sponsor at this time.", set())
        assert status == SponsorshipStatus.explicitly_unavailable

    def test_yes_phrase_skilled_worker_visa(self):
        status, _ = classify_sponsorship(
            "Corp", "Skilled worker visa sponsorship available.", set()
        )
        assert status == SponsorshipStatus.possible

    def test_yes_phrase_we_can_sponsor(self):
        status, _ = classify_sponsorship("Corp", "We can sponsor the right candidate.", set())
        assert status == SponsorshipStatus.possible

    def test_sponsorship_mentioned_requires_clarification(self):
        status, _ = classify_sponsorship(
            "Corp", "Details about sponsorship will be discussed.", set()
        )
        assert status == SponsorshipStatus.requires_clarification

    def test_no_mention_no_info(self):
        status, _ = classify_sponsorship("Corp", "Great role at a great company.", set())
        assert status == SponsorshipStatus.no_info

    def test_empty_description_no_info(self):
        status, _ = classify_sponsorship("Corp", "", set())
        assert status == SponsorshipStatus.no_info

    def test_none_description_no_info(self):
        status, _ = classify_sponsorship("Corp", None, set())
        assert status == SponsorshipStatus.no_info

    # --- Precedence rules ---

    def test_register_beats_no_phrase(self):
        # Company IS in register even though description says "unable to sponsor"
        status, _ = classify_sponsorship(
            "Revolut Ltd",
            "We are unable to sponsor visas.",
            {"revolut ltd"},
        )
        assert status == SponsorshipStatus.confirmed

    def test_no_phrase_beats_yes_phrase(self):
        # Both present → no-sponsorship phrase is checked first
        desc = "No visa sponsorship. However, skilled worker visa may be available."
        status, _ = classify_sponsorship("Corp", desc, set())
        assert status == SponsorshipStatus.explicitly_unavailable

    def test_no_phrase_beats_requires_clarification(self):
        desc = "We cannot sponsor. Sponsorship details available on request."
        status, _ = classify_sponsorship("Corp", desc, set())
        assert status == SponsorshipStatus.explicitly_unavailable

    def test_yes_phrase_beats_requires_clarification(self):
        desc = "We can sponsor. Full sponsorship arrangements are available."
        status, _ = classify_sponsorship("Corp", desc, set())
        assert status == SponsorshipStatus.possible

    def test_case_insensitive_description(self):
        status, _ = classify_sponsorship("Corp", "NO VISA SPONSORSHIP AVAILABLE.", set())
        assert status == SponsorshipStatus.explicitly_unavailable

    def test_unrelated_company_not_in_register(self):
        status, _ = classify_sponsorship("Completely Random Startup", "", REGISTER)
        assert status == SponsorshipStatus.no_info


class TestDownloadUkSponsors:
    def test_success_returns_lowercased_names(self):
        with patch("requests.get", side_effect=[_make_page_resp(), _make_csv_resp()]):
            result = download_uk_sponsors()
        assert "monzo bank limited" in result
        assert "revolut ltd" in result

    def test_header_row_excluded(self):
        # The CSV has a header "Organisation Name,..." — should not appear in result
        with patch("requests.get", side_effect=[_make_page_resp(), _make_csv_resp()]):
            result = download_uk_sponsors()
        assert "organisation name" not in result

    def test_names_stripped_of_whitespace(self):
        csv_with_spaces = (
            "Organisation Name\n"
            "  Padded Company  \n"
        )
        with patch("requests.get", side_effect=[_make_page_resp(), _make_csv_resp(csv_with_spaces)]):
            result = download_uk_sponsors()
        assert "padded company" in result

    def test_http_error_returns_empty_set(self):
        with patch("requests.get", side_effect=Exception("timeout")):
            result = download_uk_sponsors()
        assert result == set()

    def test_no_csv_url_on_page_returns_empty_set(self):
        page = MagicMock()
        page.status_code = 200
        page.text = "<html>No matching CSV links here</html>"
        page.raise_for_status = MagicMock()
        with patch("requests.get", return_value=page):
            result = download_uk_sponsors()
        assert result == set()

    def test_csv_download_error_returns_empty_set(self):
        page = _make_page_resp()
        with patch("requests.get", side_effect=[page, Exception("csv timeout")]):
            result = download_uk_sponsors()
        assert result == set()

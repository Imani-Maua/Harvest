"""Tests for api/eleanor/new_jobs/base.py filter functions."""
from datetime import date, timedelta

import pytest

from api.eleanor.new_jobs.base import (
    passes_date_filter,
    passes_deadline_filter,
    passes_description_filter,
    passes_title_filter,
)

TODAY = date.today()


class TestPassesTitleFilter:
    # --- titles that should be INCLUDED ---
    def test_junior_software_engineer(self):
        assert passes_title_filter("Junior Software Engineer") is True

    def test_graduate_backend_engineer(self):
        assert passes_title_filter("Graduate Backend Engineer") is True

    def test_new_grad_engineer(self):
        assert passes_title_filter("New Grad Software Engineer") is True

    def test_entry_level(self):
        assert passes_title_filter("Entry-Level Python Developer") is True

    def test_associate_engineer(self):
        assert passes_title_filter("Associate Software Engineer") is True

    def test_fullstack_engineer(self):
        assert passes_title_filter("Fullstack Engineer") is True

    def test_full_stack_with_space(self):
        assert passes_title_filter("Full Stack Developer") is True

    def test_python_developer(self):
        assert passes_title_filter("Python Developer") is True

    def test_software_developer(self):
        assert passes_title_filter("Software Developer") is True

    def test_case_insensitive_include(self):
        assert passes_title_filter("JUNIOR BACKEND ENGINEER") is True

    # --- titles that should be EXCLUDED ---
    def test_senior_excluded(self):
        assert passes_title_filter("Senior Software Engineer") is False

    def test_senior_abbreviated(self):
        assert passes_title_filter("Sr. Software Engineer") is False

    def test_lead_excluded(self):
        assert passes_title_filter("Lead Backend Engineer") is False

    def test_principal_excluded(self):
        assert passes_title_filter("Principal Engineer") is False

    def test_staff_engineer_excluded(self):
        assert passes_title_filter("Staff Engineer") is False

    def test_manager_excluded(self):
        assert passes_title_filter("Engineering Manager") is False

    def test_director_excluded(self):
        assert passes_title_filter("Director of Engineering") is False

    def test_head_of_excluded(self):
        assert passes_title_filter("Head of Engineering") is False

    def test_vp_excluded(self):
        assert passes_title_filter("VP of Engineering") is False

    def test_architect_excluded(self):
        assert passes_title_filter("Software Architect") is False

    # --- titles with no matching keywords → False ---
    def test_data_scientist_no_match(self):
        assert passes_title_filter("Data Scientist") is False

    def test_product_manager_no_match(self):
        assert passes_title_filter("Product Manager") is False

    def test_exclude_beats_include(self):
        # "senior" exclude wins over "software engineer" include
        assert passes_title_filter("Senior Software Engineer") is False


class TestPassesDescriptionFilter:
    def test_no_experience_mention_passes(self):
        assert passes_description_filter("We love passionate developers.") is True

    def test_empty_string_passes(self):
        assert passes_description_filter("") is True

    def test_none_passes(self):
        assert passes_description_filter(None) is True

    def test_five_plus_years_excluded(self):
        assert passes_description_filter("You will have 5+ years of Python experience.") is False

    def test_five_years_experience_phrase_excluded(self):
        assert passes_description_filter("5 years experience with distributed systems.") is False

    def test_seven_plus_years_excluded(self):
        assert passes_description_filter("7+ years working with microservices.") is False

    def test_ten_plus_years_excluded(self):
        assert passes_description_filter("10+ years experience required.") is False

    def test_minimum_5_excluded(self):
        assert passes_description_filter("Minimum 5 years of professional experience.") is False

    def test_case_insensitive_exclusion(self):
        assert passes_description_filter("MINIMUM 5 years experience required.") is False

    def test_two_years_ok(self):
        assert passes_description_filter("2 years experience welcome.") is True

    def test_three_years_ok(self):
        assert passes_description_filter("3+ years of experience preferred.") is True


class TestPassesDateFilter:
    def test_none_passes(self):
        assert passes_date_filter(None) is True

    def test_today_passes(self):
        assert passes_date_filter(TODAY) is True

    def test_twenty_days_ago_passes(self):
        assert passes_date_filter(TODAY - timedelta(days=20)) is True

    def test_twenty_one_days_ago_passes(self):
        # boundary: exactly 21 days → still within window
        assert passes_date_filter(TODAY - timedelta(days=21)) is True

    def test_twenty_two_days_ago_fails(self):
        assert passes_date_filter(TODAY - timedelta(days=22)) is False

    def test_thirty_days_ago_fails(self):
        assert passes_date_filter(TODAY - timedelta(days=30)) is False

    def test_future_date_passes(self):
        # Edge case: a future posted_date → (today - future).days is negative → within 21
        assert passes_date_filter(TODAY + timedelta(days=1)) is True


class TestPassesDeadlineFilter:
    def test_none_passes(self):
        assert passes_deadline_filter(None) is True

    def test_today_passes(self):
        # deadline == today → deadline >= today → True
        assert passes_deadline_filter(TODAY) is True

    def test_tomorrow_passes(self):
        assert passes_deadline_filter(TODAY + timedelta(days=1)) is True

    def test_yesterday_fails(self):
        assert passes_deadline_filter(TODAY - timedelta(days=1)) is False

    def test_week_ago_fails(self):
        assert passes_deadline_filter(TODAY - timedelta(days=7)) is False

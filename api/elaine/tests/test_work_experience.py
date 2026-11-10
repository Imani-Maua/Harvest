import pytest


VALID_EXPERIENCE = {
    "company": "Acme Corp",
    "title": "Software Engineer",
    "location": "London, UK",
    "start_date": "2022-01-01",
    "is_current": True,
    "description": "Built things.",
    "technologies": ["Python", "FastAPI"],
}


class TestCreateWorkExperience:
    def test_create_returns_201(self, client, auth_headers, candidate):
        res = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["company"] == "Acme Corp"
        assert data["title"] == "Software Engineer"
        assert data["candidate_id"] == candidate["id"]

    def test_create_without_auth_returns_401(self, client, candidate):
        res = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
        )
        assert res.status_code == 401

    def test_create_for_nonexistent_candidate_returns_404(self, client, auth_headers):
        res = client.post(
            "/candidates/99999/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        )
        assert res.status_code == 404

    def test_is_current_with_end_date_returns_422(self, client, auth_headers, candidate):
        payload = {**VALID_EXPERIENCE, "is_current": True, "end_date": "2023-01-01"}
        res = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_end_date_before_start_date_returns_422(self, client, auth_headers, candidate):
        payload = {
            **VALID_EXPERIENCE,
            "is_current": False,
            "start_date": "2023-01-01",
            "end_date": "2022-01-01",
        }
        res = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 422


class TestListWorkExperiences:
    def test_list_returns_200(self, client, auth_headers, candidate):
        client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        )
        res = client.get(
            f"/candidates/{candidate['id']}/work-experiences",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) == 1

    def test_list_without_auth_returns_401(self, client, candidate):
        res = client.get(f"/candidates/{candidate['id']}/work-experiences")
        assert res.status_code == 401


class TestGetWorkExperience:
    def test_get_returns_200(self, client, auth_headers, candidate):
        created = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        ).json()
        res = client.get(
            f"/candidates/{candidate['id']}/work-experiences/{created['id']}",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client, auth_headers, candidate):
        res = client.get(
            f"/candidates/{candidate['id']}/work-experiences/99999",
            headers=auth_headers,
        )
        assert res.status_code == 404


class TestUpdateWorkExperience:
    def test_update_returns_200(self, client, auth_headers, candidate):
        created = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        ).json()
        res = client.patch(
            f"/candidates/{candidate['id']}/work-experiences/{created['id']}",
            json={"title": "Senior Engineer"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["title"] == "Senior Engineer"
        assert res.json()["company"] == "Acme Corp"


class TestDeleteWorkExperience:
    def test_delete_returns_204(self, client, auth_headers, candidate):
        created = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        ).json()
        res = client.delete(
            f"/candidates/{candidate['id']}/work-experiences/{created['id']}",
            headers=auth_headers,
        )
        assert res.status_code == 204

    def test_deleted_experience_returns_404(self, client, auth_headers, candidate):
        created = client.post(
            f"/candidates/{candidate['id']}/work-experiences",
            json=VALID_EXPERIENCE,
            headers=auth_headers,
        ).json()
        client.delete(
            f"/candidates/{candidate['id']}/work-experiences/{created['id']}",
            headers=auth_headers,
        )
        res = client.get(
            f"/candidates/{candidate['id']}/work-experiences/{created['id']}",
            headers=auth_headers,
        )
        assert res.status_code == 404

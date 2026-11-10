import pytest


VALID_CANDIDATE = {
    "firstname": "Elaine",
    "lastname": "Maua",
    "email": "elaine.maua@test.com",
    "headline": "Senior Software Engineer",
    "location": "London, UK",
}


class TestCreateCandidate:
    def test_create_returns_201(self, client, auth_headers):
        res = client.post("/candidates", json=VALID_CANDIDATE, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["firstname"] == "Elaine"
        assert data["lastname"] == "Maua"
        assert data["email"] == "elaine.maua@test.com"
        assert "id" in data
        assert "created_at" in data

    def test_create_without_auth_returns_401(self, client):
        res = client.post("/candidates", json=VALID_CANDIDATE)
        assert res.status_code == 401

    def test_create_with_invalid_email_returns_422(self, client, auth_headers):
        payload = {**VALID_CANDIDATE, "email": "not-an-email"}
        res = client.post("/candidates", json=payload, headers=auth_headers)
        assert res.status_code == 422

    def test_create_with_empty_firstname_returns_422(self, client, auth_headers):
        payload = {**VALID_CANDIDATE, "firstname": ""}
        res = client.post("/candidates", json=payload, headers=auth_headers)
        assert res.status_code == 422

    def test_create_with_firstname_too_long_returns_422(self, client, auth_headers):
        payload = {**VALID_CANDIDATE, "firstname": "A" * 101}
        res = client.post("/candidates", json=payload, headers=auth_headers)
        assert res.status_code == 422


class TestGetCandidate:
    def test_get_returns_200(self, client, auth_headers, candidate):
        res = client.get(f"/candidates/{candidate['id']}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["id"] == candidate["id"]

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        res = client.get("/candidates/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_get_without_auth_returns_401(self, client, candidate):
        res = client.get(f"/candidates/{candidate['id']}")
        assert res.status_code == 401


class TestUpdateCandidate:
    def test_update_returns_200_with_changed_field(self, client, auth_headers, candidate):
        res = client.patch(
            f"/candidates/{candidate['id']}",
            json={"headline": "Principal Engineer"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["headline"] == "Principal Engineer"
        assert res.json()["firstname"] == candidate["firstname"]

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        res = client.patch("/candidates/99999", json={"headline": "X"}, headers=auth_headers)
        assert res.status_code == 404

    def test_update_without_auth_returns_401(self, client, candidate):
        res = client.patch(f"/candidates/{candidate['id']}", json={"headline": "X"})
        assert res.status_code == 401


class TestDeleteCandidate:
    def test_delete_returns_204(self, client, auth_headers, candidate):
        res = client.delete(f"/candidates/{candidate['id']}", headers=auth_headers)
        assert res.status_code == 204

    def test_deleted_candidate_returns_404(self, client, auth_headers, candidate):
        client.delete(f"/candidates/{candidate['id']}", headers=auth_headers)
        res = client.get(f"/candidates/{candidate['id']}", headers=auth_headers)
        assert res.status_code == 404

    def test_delete_without_auth_returns_401(self, client, candidate):
        res = client.delete(f"/candidates/{candidate['id']}")
        assert res.status_code == 401

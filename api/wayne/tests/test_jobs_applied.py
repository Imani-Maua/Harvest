JOBS_URL = "/jobs-applied"


class TestCreateJob:
    """POST /jobs-applied"""

    def test_no_token_returns_401(self, client):
        res = client.post(JOBS_URL, json={"company": "Acme", "job_title": "Engineer"})
        assert res.status_code == 401

    def test_missing_company_returns_422(self, client, auth_headers):
        res = client.post(JOBS_URL, json={"job_title": "Engineer"}, headers=auth_headers)
        assert res.status_code == 422

    def test_missing_job_title_returns_422(self, client, auth_headers):
        res = client.post(JOBS_URL, json={"company": "Acme"}, headers=auth_headers)
        assert res.status_code == 422

    def test_creates_job_with_required_fields(self, client, auth_headers):
        res = client.post(JOBS_URL, json={"company": "Acme", "job_title": "Engineer"}, headers=auth_headers)
        assert res.status_code == 201
        body = res.json()
        assert body["company"] == "Acme"
        assert body["job_title"] == "Engineer"
        assert body["job_status"] == "watch_list"
        assert "id" in body
        assert "created_at" in body

    def test_creates_job_with_all_fields(self, client, auth_headers):
        res = client.post(
            JOBS_URL,
            json={
                "company": "Acme",
                "job_title": "Engineer",
                "job_status": "applied",
                "location": "London",
                "job_url": "https://example.com/job",
                "applied_date": "2026-01-15",
                "notes": "Looks exciting",
            },
            headers=auth_headers,
        )
        assert res.status_code == 201
        body = res.json()
        assert body["job_status"] == "applied"
        assert body["location"] == "London"
        assert body["applied_date"] == "2026-01-15"

    def test_invalid_job_status_returns_422(self, client, auth_headers):
        res = client.post(
            JOBS_URL,
            json={"company": "Acme", "job_title": "Engineer", "job_status": "ghosted"},
            headers=auth_headers,
        )
        assert res.status_code == 422


class TestGetJob:
    """GET /jobs-applied/{job_id}"""

    def test_no_token_returns_401(self, client, a_job):
        res = client.get(f"{JOBS_URL}/{a_job['id']}")
        assert res.status_code == 401

    def test_missing_job_returns_404(self, client, auth_headers):
        res = client.get(f"{JOBS_URL}/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_returns_correct_job(self, client, auth_headers, a_job):
        res = client.get(f"{JOBS_URL}/{a_job['id']}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["id"] == a_job["id"]
        assert res.json()["company"] == "Acme"


class TestListJobs:
    """GET /jobs-applied"""

    def test_no_token_returns_401(self, client):
        res = client.get(JOBS_URL)
        assert res.status_code == 401

    def test_returns_empty_list_when_no_jobs(self, client, auth_headers):
        res = client.get(JOBS_URL, headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_all_jobs(self, client, auth_headers):
        client.post(JOBS_URL, json={"company": "Acme", "job_title": "Engineer"}, headers=auth_headers)
        client.post(JOBS_URL, json={"company": "BigCo", "job_title": "Manager"}, headers=auth_headers)
        res = client.get(JOBS_URL, headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestUpdateJob:
    """PATCH /jobs-applied/{job_id}"""

    def test_no_token_returns_401(self, client, a_job):
        res = client.patch(f"{JOBS_URL}/{a_job['id']}", json={"job_status": "applied"})
        assert res.status_code == 401

    def test_missing_job_returns_404(self, client, auth_headers):
        res = client.patch(f"{JOBS_URL}/99999", json={"job_status": "applied"}, headers=auth_headers)
        assert res.status_code == 404

    def test_updates_only_provided_field(self, client, auth_headers, a_job):
        res = client.patch(
            f"{JOBS_URL}/{a_job['id']}",
            json={"job_status": "in_pipeline"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["job_status"] == "in_pipeline"
        assert body["company"] == "Acme"

    def test_invalid_status_returns_422(self, client, auth_headers, a_job):
        res = client.patch(
            f"{JOBS_URL}/{a_job['id']}",
            json={"job_status": "ghosted"},
            headers=auth_headers,
        )
        assert res.status_code == 422


class TestDeleteJob:
    """DELETE /jobs-applied/{job_id}"""

    def test_no_token_returns_401(self, client, a_job):
        res = client.delete(f"{JOBS_URL}/{a_job['id']}")
        assert res.status_code == 401

    def test_missing_job_returns_404(self, client, auth_headers):
        res = client.delete(f"{JOBS_URL}/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_delete_returns_204(self, client, auth_headers, a_job):
        res = client.delete(f"{JOBS_URL}/{a_job['id']}", headers=auth_headers)
        assert res.status_code == 204

    def test_deleted_job_no_longer_found(self, client, auth_headers, a_job):
        client.delete(f"{JOBS_URL}/{a_job['id']}", headers=auth_headers)
        res = client.get(f"{JOBS_URL}/{a_job['id']}", headers=auth_headers)
        assert res.status_code == 404

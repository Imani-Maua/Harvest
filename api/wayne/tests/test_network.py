NETWORK_URL = "/network"
JOBS_URL = "/jobs-applied"


class TestCreateNetwork:
    """POST /network"""

    def test_no_token_returns_401(self, client, a_job):
        res = client.post(NETWORK_URL, json={"job_applied_id": a_job["id"]})
        assert res.status_code == 401

    def test_creates_network_record(self, client, auth_headers, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "hiring_manager": "jane@acme.com", "hiring_name": "Jane"},
            headers=auth_headers,
        )
        assert res.status_code == 201
        body = res.json()
        assert body["job_applied_id"] == a_job["id"]
        assert body["hiring_manager"] == "jane@acme.com"

    def test_duplicate_job_id_returns_409(self, client, auth_headers, a_network, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"]},
            headers=auth_headers,
        )
        assert res.status_code == 409

    def test_invalid_hiring_manager_email_returns_422(self, client, auth_headers, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "hiring_manager": "not-an-email"},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_invalid_recruiter_email_returns_422(self, client, auth_headers, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "technical_recruiter": "not-an-email"},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_invalid_peer_email_in_array_returns_422(self, client, auth_headers, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "peers": ["valid@acme.com", "not-an-email"]},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_all_peers_valid_emails_accepted(self, client, auth_headers, a_job):
        res = client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "peers": ["alice@acme.com", "bob@acme.com"]},
            headers=auth_headers,
        )
        assert res.status_code == 201
        assert res.json()["peers"] == ["alice@acme.com", "bob@acme.com"]


class TestGetNetwork:
    """GET /network/{network_id}"""

    def test_no_token_returns_401(self, client, a_network):
        res = client.get(f"{NETWORK_URL}/{a_network['id']}")
        assert res.status_code == 401

    def test_missing_network_returns_404(self, client, auth_headers):
        res = client.get(f"{NETWORK_URL}/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_returns_correct_network(self, client, auth_headers, a_network):
        res = client.get(f"{NETWORK_URL}/{a_network['id']}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["id"] == a_network["id"]
        assert res.json()["hiring_manager"] == "jane@acme.com"


class TestGetNetworkByJob:
    """GET /network/by-job/{job_id}"""

    def test_no_token_returns_401(self, client, a_network, a_job):
        res = client.get(f"{NETWORK_URL}/by-job/{a_job['id']}")
        assert res.status_code == 401

    def test_missing_job_network_returns_404(self, client, auth_headers):
        res = client.get(f"{NETWORK_URL}/by-job/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_returns_network_for_job(self, client, auth_headers, a_network, a_job):
        res = client.get(f"{NETWORK_URL}/by-job/{a_job['id']}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["job_applied_id"] == a_job["id"]


class TestUpdateNetwork:
    """PATCH /network/{network_id}"""

    def test_no_token_returns_401(self, client, a_network):
        res = client.patch(f"{NETWORK_URL}/{a_network['id']}", json={"hiring_name": "New Name"})
        assert res.status_code == 401

    def test_missing_network_returns_404(self, client, auth_headers):
        res = client.patch(f"{NETWORK_URL}/99999", json={"hiring_name": "New Name"}, headers=auth_headers)
        assert res.status_code == 404

    def test_updates_only_provided_fields(self, client, auth_headers, a_network):
        res = client.patch(
            f"{NETWORK_URL}/{a_network['id']}",
            json={"hiring_name": "Updated Name"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["hiring_name"] == "Updated Name"
        assert body["hiring_manager"] == "jane@acme.com"

    def test_invalid_email_on_update_returns_422(self, client, auth_headers, a_network):
        res = client.patch(
            f"{NETWORK_URL}/{a_network['id']}",
            json={"technical_recruiter": "not-an-email"},
            headers=auth_headers,
        )
        assert res.status_code == 422


class TestDeleteNetwork:
    """DELETE /network/{network_id}"""

    def test_no_token_returns_401(self, client, a_network):
        res = client.delete(f"{NETWORK_URL}/{a_network['id']}")
        assert res.status_code == 401

    def test_missing_network_returns_404(self, client, auth_headers):
        res = client.delete(f"{NETWORK_URL}/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_delete_returns_204(self, client, auth_headers, a_network):
        res = client.delete(f"{NETWORK_URL}/{a_network['id']}", headers=auth_headers)
        assert res.status_code == 204

    def test_deleted_network_no_longer_found(self, client, auth_headers, a_network):
        client.delete(f"{NETWORK_URL}/{a_network['id']}", headers=auth_headers)
        res = client.get(f"{NETWORK_URL}/{a_network['id']}", headers=auth_headers)
        assert res.status_code == 404

class TestGetByCompany:
    """GET /network/by-company/{company}"""

    def test_no_token_returns_401(self, client):
        res = client.get(f"{NETWORK_URL}/by-company/Acme")
        assert res.status_code == 401

    def test_unknown_company_returns_empty_list(self, client, auth_headers):
        res = client.get(f"{NETWORK_URL}/by-company/NoSuchCorp", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_company_with_job_but_no_network_returns_empty_list(self, client, auth_headers, a_job):
        res = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_match_is_exact_case_sensitive(self, client, auth_headers, a_network):
        res = client.get(f"{NETWORK_URL}/by-company/acme", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_hiring_manager_contact(self, client, auth_headers, a_network):
        res = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers)
        assert res.status_code == 200
        contacts = res.json()
        managers = [c for c in contacts if c["role"] == "hiring_manager"]
        assert len(managers) == 1
        assert managers[0]["email"] == "jane@acme.com"
        assert managers[0]["name"] == "Jane Smith"

    def test_returns_technical_recruiter_contact(self, client, auth_headers, a_network):
        contacts = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers).json()
        recruiters = [c for c in contacts if c["role"] == "technical_recruiter"]
        assert len(recruiters) == 1
        assert recruiters[0]["email"] == "bob@acme.com"
        assert recruiters[0]["name"] == "Bob Lee"

    def test_returns_peer_contacts(self, client, auth_headers, a_network):
        contacts = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers).json()
        peers = [c for c in contacts if c["role"] == "peer"]
        assert len(peers) == 1
        assert peers[0]["email"] == "alice@acme.com"
        assert peers[0]["name"] == "Alice Wu"

    def test_multiple_peers_each_become_separate_contact(self, client, auth_headers, a_job):
        client.post(
            NETWORK_URL,
            json={
                "job_applied_id": a_job["id"],
                "peers": ["p1@acme.com", "p2@acme.com", "p3@acme.com"],
                "peer_name": "Team",
            },
            headers=auth_headers,
        )
        contacts = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers).json()
        peers = [c for c in contacts if c["role"] == "peer"]
        assert len(peers) == 3
        assert {c["email"] for c in peers} == {"p1@acme.com", "p2@acme.com", "p3@acme.com"}

    def test_contacts_aggregated_across_multiple_jobs_at_same_company(self, client, auth_headers, a_job):
        second_job = client.post(
            JOBS_URL,
            json={"company": "Acme", "job_title": "Manager"},
            headers=auth_headers,
        ).json()
        client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "hiring_manager": "jane@acme.com", "hiring_name": "Jane"},
            headers=auth_headers,
        )
        client.post(
            NETWORK_URL,
            json={"job_applied_id": second_job["id"], "hiring_manager": "dan@acme.com", "hiring_name": "Dan"},
            headers=auth_headers,
        )
        contacts = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers).json()
        managers = [c for c in contacts if c["role"] == "hiring_manager"]
        assert len(managers) == 2
        assert {c["email"] for c in managers} == {"jane@acme.com", "dan@acme.com"}

    def test_only_populated_fields_produce_contacts(self, client, auth_headers, a_job):
        client.post(
            NETWORK_URL,
            json={"job_applied_id": a_job["id"], "hiring_manager": "jane@acme.com", "hiring_name": "Jane"},
            headers=auth_headers,
        )
        contacts = client.get(f"{NETWORK_URL}/by-company/Acme", headers=auth_headers).json()
        assert all(c["role"] == "hiring_manager" for c in contacts)
        assert len(contacts) == 1

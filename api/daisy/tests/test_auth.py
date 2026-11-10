LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"
SET_PASSWORD_URL = "/auth/set_new_password"


class TestLogin:
    """POST /auth/login?key=<secret>"""

    def test_missing_key_returns_404(self, client, test_user):
        res = client.post(LOGIN_URL, json={"email": "elaine@test.com", "password": "correct-password-123"})
        assert res.status_code == 404

    def test_wrong_key_returns_404(self, client, test_user):
        res = client.post(f"{LOGIN_URL}?key=bad-key", json={"email": "elaine@test.com", "password": "correct-password-123"})
        assert res.status_code == 404

    def test_wrong_password_returns_401(self, client, test_user, login_secret):
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "elaine@test.com", "password": "wrong-password"})
        assert res.status_code == 401

    def test_wrong_email_returns_401(self, client, test_user, login_secret):
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "ghost@test.com", "password": "correct-password-123"})
        assert res.status_code == 401

    def test_successful_login_returns_token_and_firstname(self, client, test_user, login_secret):
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "elaine@test.com", "password": "correct-password-123"})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["firstname"] == "Elaine"

    def test_inactive_user_cannot_login(self, client, inactive_user, login_secret):
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "inactive@test.com", "password": "some-password"})
        assert res.status_code == 403


class TestMe:
    """GET /auth/me"""

    def test_no_token_returns_401(self, client):
        res = client.get(ME_URL)
        assert res.status_code == 401

    def test_invalid_token_returns_401(self, client):
        res = client.get(ME_URL, headers={"Authorization": "Bearer not.a.real.token"})
        assert res.status_code == 401

    def test_valid_token_returns_user(self, client, test_user, auth_headers):
        res = client.get(ME_URL, headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["email"] == "elaine@test.com"
        assert body["firstname"] == "Elaine"
        assert "id" in body


class TestSetNewPassword:
    """POST /auth/set_new_password"""

    def test_no_token_returns_401(self, client, test_user):
        res = client.post(SET_PASSWORD_URL, json={"current_password": "correct-password-123", "new_password": "new-pass-456"})
        assert res.status_code == 401

    def test_wrong_current_password_returns_401(self, client, test_user, auth_headers):
        res = client.post(SET_PASSWORD_URL, json={"current_password": "wrong-password", "new_password": "new-pass-456"}, headers=auth_headers)
        assert res.status_code == 401

    def test_successful_password_change_returns_message(self, client, test_user, auth_headers):
        res = client.post(SET_PASSWORD_URL, json={"current_password": "correct-password-123", "new_password": "new-pass-456"}, headers=auth_headers)
        assert res.status_code == 200
        assert "message" in res.json()

    def test_old_password_rejected_after_change(self, client, test_user, auth_headers, login_secret):
        client.post(SET_PASSWORD_URL, json={"current_password": "correct-password-123", "new_password": "new-pass-456"}, headers=auth_headers)
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "elaine@test.com", "password": "correct-password-123"})
        assert res.status_code == 401

    def test_new_password_works_after_change(self, client, test_user, auth_headers, login_secret):
        client.post(SET_PASSWORD_URL, json={"current_password": "correct-password-123", "new_password": "new-pass-456"}, headers=auth_headers)
        res = client.post(f"{LOGIN_URL}?key={login_secret}", json={"email": "elaine@test.com", "password": "new-pass-456"})
        assert res.status_code == 200

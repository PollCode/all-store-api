"""Tests para POST /api/v1/auth/logout"""
import pytest

from ...tests.factories import make_access_token, make_refresh_token, make_user

pytestmark = pytest.mark.auth

LOGOUT_URL = "/api/v1/auth/logout"
USERS_URL = "/api/v1/users"


class TestAuthLogout:

    def test_logout_revokes_access_token(self, client, db):
        """Tras logout, el access token deja de servir."""
        user = make_user(db, email="logout@test.com", role="admin")
        access = make_access_token(user)
        refresh = make_refresh_token(db, user)

        # Antes: el token funciona
        ok = client.get(USERS_URL, headers={"Authorization": f"Bearer {access}"})
        assert ok.status_code == 200

        # Logout
        logout = client.post(
            LOGOUT_URL,
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout.status_code == 204

        # Después: el access token está revocado
        revoked = client.get(USERS_URL, headers={"Authorization": f"Bearer {access}"})
        assert revoked.status_code == 401
        assert "revoked" in revoked.text.lower()

    def test_logout_without_token_returns_401(self, client):
        """Logout sin token de acceso devuelve 401."""
        response = client.post(LOGOUT_URL, json={})

        assert response.status_code == 401

    def test_logout_all_devices_revokes_all_refresh_tokens(self, client, db):
        """Con all_devices=true, todos los refresh tokens del usuario quedan revocados."""
        user = make_user(db, email="multi@test.com", role="buyer")
        access = make_access_token(user)
        r1 = make_refresh_token(db, user)
        r2 = make_refresh_token(db, user)

        response = client.post(
            LOGOUT_URL,
            json={"all_devices": True},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == 204

        # Ninguno de los dos refresh tokens debe poder usarse
        for token in (r1, r2):
            r = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
            assert r.status_code == 401
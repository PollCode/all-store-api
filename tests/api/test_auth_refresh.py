"""Tests para POST /api/v1/auth/refresh"""
import pytest

from ...tests.factories import make_refresh_token, make_user

pytestmark = pytest.mark.auth

REFRESH_URL = "/api/v1/auth/refresh"


class TestAuthRefresh:

    def test_refresh_success_returns_new_tokens(self, client, db):
        """Un refresh válido devuelve un nuevo par de tokens."""
        user = make_user(db, email="refresh@test.com")
        old_refresh = make_refresh_token(db, user)

        response = client.post(REFRESH_URL, json={"refresh_token": old_refresh})

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        # Rotación: el refresh token devuelto es distinto al usado
        assert body["refresh_token"] != old_refresh

    def test_refresh_with_invalid_token_returns_401(self, client, db):
        """Un token malformado o con firma inválida devuelve 401."""
        response = client.post(
            REFRESH_URL,
            json={"refresh_token": "not.a.valid.jwt"},
        )

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.text

    def test_refresh_with_revoked_token_returns_401(self, client, db):
        """Un refresh token ya usado (revocado) no puede reutilizarse."""
        user = make_user(db, email="revoked@test.com")
        old_refresh = make_refresh_token(db, user)

        # Primer uso → OK, revoca el token
        first = client.post(REFRESH_URL, json={"refresh_token": old_refresh})
        assert first.status_code == 200

        # Segundo uso del mismo → 401
        second = client.post(REFRESH_URL, json={"refresh_token": old_refresh})
        assert second.status_code == 401
        assert "revoked" in second.text.lower()
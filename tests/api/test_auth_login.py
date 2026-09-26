"""Tests para POST /api/v1/auth/login"""
import pytest

from ...tests.factories import make_user

pytestmark = pytest.mark.auth

LOGIN_URL = "/api/v1/auth/login"


class TestAuthLogin:

    def test_login_success_returns_tokens(self, client, db):
        """Login con credenciales válidas devuelve access y refresh token."""
        make_user(db, email="ok@test.com", password="Secret123!", role="buyer")

        response = client.post(
            LOGIN_URL,
            json={"email": "ok@test.com", "password": "Secret123!"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0
        assert len(body["access_token"].split(".")) == 3  # JWT tiene 3 partes

    def test_login_wrong_password_returns_401(self, client, db):
        """Contraseña incorrecta devuelve 401 con mensaje genérico."""
        make_user(db, email="wp@test.com", password="CorrectPass123!")

        response = client.post(
            LOGIN_URL,
            json={"email": "wp@test.com", "password": "WrongPass!"},
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.text

    def test_login_unknown_email_returns_401(self, client, db):
        """Email no registrado devuelve 401 (sin filtrar si existe o no)."""
        response = client.post(
            LOGIN_URL,
            json={"email": "ghost@test.com", "password": "Whatever123!"},
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.text
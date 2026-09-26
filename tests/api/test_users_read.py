"""Tests para GET /api/v1/users/{id}"""
import uuid

import pytest

pytestmark = pytest.mark.users

USERS_URL = "/api/v1/users"


class TestUsersRead:

    def test_get_user_by_id_success(self, client, buyer_user, admin_headers):
        """Obtener un usuario existente por ID devuelve sus datos."""
        response = client.get(
            f"{USERS_URL}/{buyer_user.id}", headers=admin_headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(buyer_user.id)
        assert body["email"] == buyer_user.email
        assert body["role"] == "buyer"

    def test_get_user_not_found_returns_404(self, client, admin_headers):
        """ID inexistente devuelve 404."""
        random_id = uuid.uuid4()
        response = client.get(f"{USERS_URL}/{random_id}", headers=admin_headers)

        assert response.status_code == 404
        assert str(random_id) in response.text

    def test_get_user_without_token_returns_401(self, client, buyer_user):
        """Sin token, el endpoint devuelve 401 Not authenticated."""
        response = client.get(f"{USERS_URL}/{buyer_user.id}")

        assert response.status_code == 401
        assert "Not authenticated" in response.text
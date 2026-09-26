"""Tests para PATCH /api/v1/users/{id} y PATCH /api/v1/users/bulk"""
import uuid

import pytest

from ...tests.factories import make_user

pytestmark = pytest.mark.users

USERS_URL = "/api/v1/users"
BULK_URL = "/api/v1/users/bulk"


class TestUsersUpdate:

    def test_admin_can_update_any_user(self, client, db, admin_headers):
        """Admin puede modificar el perfil de cualquier usuario."""
        target = make_user(db, email="target@test.com", full_name="Old Name")

        response = client.patch(
            f"{USERS_URL}/{target.id}",
            json={"full_name": "New Name", "role": "seller"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["full_name"] == "New Name"
        assert body["role"] == "seller"

    def test_user_can_update_own_profile(self, client, buyer_user, buyer_headers):
        """Un usuario puede modificar su propio perfil."""
        response = client.patch(
            f"{USERS_URL}/{buyer_user.id}",
            json={"full_name": "Updated Buyer"},
            headers=buyer_headers,
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Buyer"

    def test_user_cannot_update_other_user_returns_403(
        self, client, db, buyer_headers
    ):
        """Un usuario no puede modificar el perfil de otro."""
        other = make_user(db, email="other@test.com")

        response = client.patch(
            f"{USERS_URL}/{other.id}",
            json={"full_name": "Hacked"},
            headers=buyer_headers,
        )

        assert response.status_code == 403
        assert "own profile" in response.text


class TestUsersBulkUpdate:

    def test_bulk_update_success(self, client, db, admin_headers):
        """Admin actualiza varios usuarios a la vez."""
        u1 = make_user(db, email="bu1@test.com", role="buyer")
        u2 = make_user(db, email="bu2@test.com", role="buyer")

        payload = [
            {"id": str(u1.id), "role": "seller"},
            {"id": str(u2.id), "full_name": "Renamed"},
        ]

        response = client.patch(BULK_URL, json=payload, headers=admin_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["updated"] == 2
        by_id = {item["id"]: item for item in body["items"]}
        assert by_id[str(u1.id)]["role"] == "seller"
        assert by_id[str(u2.id)]["full_name"] == "Renamed"

    def test_bulk_update_missing_ids_returns_404(self, client, db, admin_headers):
        """Si alguno de los IDs no existe, devuelve 404."""
        real = make_user(db, email="real@test.com")
        fake_id = uuid.uuid4()

        payload = [
            {"id": str(real.id), "full_name": "OK"},
            {"id": str(fake_id), "full_name": "Ghost"},
        ]

        response = client.patch(BULK_URL, json=payload, headers=admin_headers)

        assert response.status_code == 404
        assert str(fake_id) in response.text

    def test_bulk_update_without_admin_returns_403(self, client, db, buyer_headers):
        """Un buyer no puede hacer bulk update."""
        target = make_user(db, email="bu3@test.com")

        payload = [{"id": str(target.id), "full_name": "X"}]

        response = client.patch(BULK_URL, json=payload, headers=buyer_headers)

        assert response.status_code == 403
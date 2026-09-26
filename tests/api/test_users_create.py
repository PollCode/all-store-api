"""Tests para POST /api/v1/users y POST /api/v1/users/bulk"""
import pytest

from tests.factories import make_user

pytestmark = pytest.mark.users

USERS_URL = "/api/v1/users"
BULK_URL = "/api/v1/users/bulk"


class TestUsersCreate:

    def test_create_user_success(self, client, db, admin_headers):
        """Admin crea un usuario correctamente y la respuesta no filtra el hash."""
        payload = {
            "email": "nuevo@test.com",
            "password": "Password123!",
            "full_name": "Nuevo Usuario",
            "role": "buyer",
            "is_active": True,
        }

        response = client.post(USERS_URL, json=payload, headers=admin_headers)

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "nuevo@test.com"
        assert body["role"] == "buyer"
        assert "password" not in body
        assert "password_hash" not in body
        assert "id" in body

    def test_create_user_duplicate_email_returns_409(self, client, db, admin_headers):
        """Crear un usuario con email ya registrado devuelve 409."""
        make_user(db, email="dup@test.com")

        response = client.post(
            USERS_URL,
            json={
                "email": "dup@test.com",
                "password": "Password123!",
                "full_name": "Duplicado",
                "role": "buyer",
            },
            headers=admin_headers,
        )

        assert response.status_code == 409
        assert "dup@test.com" in response.text

    def test_create_user_without_admin_returns_403(self, client, buyer_headers):
        """Un usuario con rol buyer no puede crear usuarios."""
        response = client.post(
            USERS_URL,
            json={
                "email": "x@test.com",
                "password": "Password123!",
                "full_name": "X",
                "role": "buyer",
            },
            headers=buyer_headers,
        )

        assert response.status_code == 403
        assert "Admin privileges required" in response.text


class TestUsersBulkCreate:

    def test_bulk_create_success(self, client, admin_headers):
        """Crear varios usuarios de una vez devuelve la lista creada."""
        payload = [
            {
                "email": f"bulk{i}@test.com",
                "password": "Password123!",
                "full_name": f"Bulk {i}",
                "role": "buyer",
            }
            for i in range(3)
        ]

        response = client.post(BULK_URL, json=payload, headers=admin_headers)

        assert response.status_code == 201
        body = response.json()
        assert body["created"] == 3
        assert len(body["items"]) == 3
        emails = {item["email"] for item in body["items"]}
        assert emails == {"bulk0@test.com", "bulk1@test.com", "bulk2@test.com"}

    def test_bulk_create_duplicate_in_payload_returns_400(
        self, client, admin_headers
    ):
        """Emails duplicados dentro del payload devuelven 400."""
        payload = [
            {
                "email": "same@test.com",
                "password": "Password123!",
                "full_name": "A",
                "role": "buyer",
            },
            {
                "email": "same@test.com",
                "password": "Password123!",
                "full_name": "B",
                "role": "buyer",
            },
        ]

        response = client.post(BULK_URL, json=payload, headers=admin_headers)

        assert response.status_code == 400
        assert "Duplicate" in response.text

    def test_bulk_create_email_already_in_db_returns_409(
        self, client, db, admin_headers
    ):
        """Si uno de los emails ya existe en la BD, devuelve 409."""
        make_user(db, email="taken@test.com")

        payload = [
            {
                "email": "free@test.com",
                "password": "Password123!",
                "full_name": "Free",
                "role": "buyer",
            },
            {
                "email": "taken@test.com",
                "password": "Password123!",
                "full_name": "Taken",
                "role": "buyer",
            },
        ]

        response = client.post(BULK_URL, json=payload, headers=admin_headers)

        assert response.status_code == 409
        assert "taken@test.com" in response.text
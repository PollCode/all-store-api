"""Tests para DELETE /api/v1/users/{id}"""
import uuid

import pytest
from sqlmodel import Session

from models.users import User
from ...tests.factories import make_user

pytestmark = pytest.mark.users

USERS_URL = "/api/v1/users"


class TestUsersDelete:

    def test_admin_can_delete_user(self, client, db, admin_headers):
        """Admin elimina un usuario y desaparece de la BD."""
        target = make_user(db, email="todelete@test.com")
        target_id = target.id

        response = client.delete(
            f"{USERS_URL}/{target_id}", headers=admin_headers
        )

        assert response.status_code == 204
        db.expire_all()  # limpia caché de sesión
        assert db.get(User, target_id) is None

    def test_delete_user_without_admin_returns_403(self, client, db, buyer_headers):
        """Un buyer no puede eliminar usuarios."""
        target = make_user(db, email="protected@test.com")

        response = client.delete(
            f"{USERS_URL}/{target.id}", headers=buyer_headers
        )

        assert response.status_code == 403

    def test_delete_non_existent_user_returns_404(self, client, admin_headers):
        """Eliminar un ID inexistente devuelve 404."""
        random_id = uuid.uuid4()

        response = client.delete(
            f"{USERS_URL}/{random_id}", headers=admin_headers
        )

        assert response.status_code == 404
        assert str(random_id) in response.text
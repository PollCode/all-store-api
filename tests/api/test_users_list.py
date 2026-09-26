"""Tests para GET /api/v1/users"""
import pytest

from ...tests.factories import make_user

pytestmark = pytest.mark.users

USERS_URL = "/api/v1/users"


class TestUsersList:

    def test_list_users_returns_paginated_response(self, client, db, admin_headers):
        """Listar usuarios devuelve estructura paginada correcta."""
        for i in range(3):
            make_user(db, email=f"u{i}@test.com", role="buyer")

        response = client.get(USERS_URL, headers=admin_headers)

        assert response.status_code == 200
        body = response.json()
        assert {"items", "total", "page", "page_size", "pages"} <= body.keys()
        # 3 buyers + 1 admin (fixture) = 4
        assert body["total"] == 4
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert len(body["items"]) == 4

    def test_list_users_filters_by_role(self, client, db, admin_headers):
        """El filtro `role=seller` sólo devuelve vendedores."""
        make_user(db, email="s1@test.com", role="seller")
        make_user(db, email="s2@test.com", role="seller")
        make_user(db, email="b1@test.com", role="buyer")

        response = client.get(
            USERS_URL, params={"role": "seller"}, headers=admin_headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert all(item["role"] == "seller" for item in body["items"])

    def test_list_users_pagination_respects_page_size(
        self, client, db, admin_headers
    ):
        """page_size limita la cantidad de items devueltos."""
        for i in range(5):
            make_user(db, email=f"p{i}@test.com", role="buyer")

        response = client.get(
            USERS_URL,
            params={"page": 1, "page_size": 2},
            headers=admin_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 6      # 5 + admin
        assert len(body["items"]) == 2
        assert body["pages"] == 3
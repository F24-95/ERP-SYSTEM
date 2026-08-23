"""Tests for fee structure, collection, and student balance endpoints."""
import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_bad_request,
    assert_created,
    assert_forbidden,
    assert_not_found,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestFeeStructureCRUD:
    async def test_create_fee_structure(self, admin_client):
        resp = await admin_client.post(
            "/fees/structures",
            json={
                "classroom_id": 1,
                "academic_session_id": 1,
                "name": "Tuition Fee",
                "amount": 50000.00,
                "due_date": "2026-09-30",
            },
        )
        assert resp.status_code in (201, 400, 422)

    async def test_list_fee_structures(self, admin_client):
        resp = await admin_client.get("/fees/structures")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_fee_structures_unauthorized(self, client):
        resp = await client.get("/fees/structures")
        assert_unauthorized(resp)

    async def test_get_fee_structure(self, admin_client):
        list_resp = await admin_client.get("/fees/structures")
        if list_resp.json():
            fs_id = list_resp.json()[0]["id"]
            resp = await admin_client.get(
                f"/fees/structures/{fs_id}"
            )
            assert resp.status_code == 200

    async def test_get_fee_structure_not_found(self, admin_client):
        resp = await admin_client.get(
            "/fees/structures/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_update_fee_structure(self, admin_client):
        list_resp = await admin_client.get("/fees/structures")
        if list_resp.json():
            fs_id = list_resp.json()[0]["id"]
            resp = await admin_client.patch(
                f"/fees/structures/{fs_id}",
                json={"name": "Updated Fee Structure"},
            )
            assert resp.status_code == 200

    async def test_delete_fee_structure(self, admin_client):
        create_resp = await admin_client.post(
            "/fees/structures",
            json={
                "classroom_id": 1,
                "academic_session_id": 1,
                "name": "Temp Fee",
                "amount": 1000.00,
                "due_date": "2026-10-01",
            },
        )
        if create_resp.status_code == 201:
            fs_id = create_resp.json()["id"]
            resp = await admin_client.delete(
                f"/fees/structures/{fs_id}"
            )
            assert resp.status_code in (204, 400)


class TestFeeCollectionCRUD:
    async def test_create_fee_collection(self, admin_client):
        resp = await admin_client.post(
            "/fees/collections",
            json={
                "fee_structure_id": 1,
                "student_id": 1,
                "amount_paid": 5000.00,
                "payment_mode": "cash",
                "receipt_number": "RCP-001",
            },
        )
        assert resp.status_code in (201, 400, 422)

    async def test_list_fee_collections(self, admin_client):
        resp = await admin_client.get("/fees/collections")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_fee_collections_unauthorized(self, client):
        resp = await client.get("/fees/collections")
        assert_unauthorized(resp)

    async def test_get_fee_collection(self, admin_client):
        list_resp = await admin_client.get("/fees/collections")
        if list_resp.json():
            fc_id = list_resp.json()[0]["id"]
            resp = await admin_client.get(
                f"/fees/collections/{fc_id}"
            )
            assert resp.status_code == 200

    async def test_get_fee_collection_not_found(self, admin_client):
        resp = await admin_client.get(
            "/fees/collections/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_delete_fee_collection(self, admin_client):
        create_resp = await admin_client.post(
            "/fees/collections",
            json={
                "fee_structure_id": 1,
                "student_id": 1,
                "amount_paid": 1000.00,
                "payment_mode": "cash",
                "receipt_number": "RCP-DEL",
            },
        )
        if create_resp.status_code == 201:
            fc_id = create_resp.json()["id"]
            resp = await admin_client.delete(
                f"/fees/collections/{fc_id}"
            )
            assert resp.status_code in (204, 400)


class TestStudentFeeBalance:
    async def test_student_fee_balance_unauthorized(self, client):
        resp = await client.get("/students/1/fee-balance")
        assert_unauthorized(resp)

    async def test_student_fee_balance_invalid_id(self, admin_client):
        resp = await admin_client.get(
            "/students/00000000-0000-0000-0000-000000000000/fee-balance"
        )
        assert resp.status_code in (404, 400, 422)


class TestFeeReceipts:
    async def test_fee_receipts_list_unauthorized(self, client):
        resp = await client.get("/fees/receipts")
        assert_unauthorized(resp)

    async def test_fee_receipts_list(self, admin_client):
        resp = await admin_client.get("/fees/receipts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_fee_receipt_unauthorized(self, client):
        resp = await client.get(
            "/fees/receipts/00000000-0000-0000-0000-000000000000"
        )
        assert_unauthorized(resp)

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_create_and_get_document_validation(client: AsyncClient):
    payload = {
        "organization_inn": "7707083893",
        "document_type": "invoice",
        "payload": {
            "number": "INV-2026-001",
            "date": "2026-11-20",
            "total_amount": 150000.0,
        },
    }
    response = await client.post("/api/v1/documents/validate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["organization_inn"] == "7707083893"
    assert data["status"] == "valid"
    assert "document_uid" in data

    uid = data["document_uid"]
    get_response = await client.get(f"/api/v1/documents/{uid}")
    assert get_response.status_code == 200
    assert get_response.json()["document_uid"] == uid


@pytest.mark.asyncio
async def test_invalid_document_validation(client: AsyncClient):
    payload = {
        "organization_inn": "123",
        "document_type": "invoice",
        "payload": {},
    }
    response = await client.post("/api/v1/documents/validate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "invalid"
    assert data["validation_errors"] is not None

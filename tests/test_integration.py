from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_create_certificate_request(client: AsyncClient):
    payload = {
        "inn": "7707083893",
        "kpp": "770701001",
        "organization_name": 'ПАО "Сбербанк"',
        "applicant_full_name": "Иванов Иван Иванович",
        "applicant_snils": "112-233-445 95",
    }
    response = await client.post("/api/v1/requests", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "DRAFT"
    assert data["applicant_full_name"] == "Иванов Иван Иванович"
    assert data["applicant_snils"] == "11223344595"
    assert data["organization"]["inn"] == "7707083893"
    assert data["organization"]["name"] == 'ПАО "Сбербанк"'


@pytest.mark.asyncio
async def test_create_request_idempotency(client: AsyncClient):
    payload = {
        "inn": "7707083893",
        "organization_name": 'ООО "Вектор"',
        "applicant_full_name": "Петров Петр Сергеевич",
        "applicant_snils": "112-233-445 95",
    }
    headers = {"X-Idempotency-Key": "req-idem-482a-bc91"}

    first = await client.post("/api/v1/requests", json=payload, headers=headers)
    assert first.status_code == 201
    first_data = first.json()

    second = await client.post("/api/v1/requests", json=payload, headers=headers)
    assert second.status_code in (200, 201)
    second_data = second.json()

    assert first_data["id"] == second_data["id"]
    assert second_data["idempotency_key"] == "req-idem-482a-bc91"

    list_res = await client.get("/api/v1/requests")
    assert list_res.status_code == 200
    matched = [r for r in list_res.json() if r["idempotency_key"] == "req-idem-482a-bc91"]
    assert len(matched) == 1


@pytest.mark.asyncio
async def test_reject_invalid_inn_checksum(client: AsyncClient):
    response = await client.post(
        "/api/v1/requests",
        json={
            "inn": "7707083894",
            "organization_name": 'ООО "Тест"',
            "applicant_full_name": "Сидоров Алексей",
            "applicant_snils": "112-233-445 95",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("INN" in str(err) for err in data["detail"])


@pytest.mark.asyncio
async def test_reject_invalid_snils_checksum(client: AsyncClient):
    response = await client.post(
        "/api/v1/requests",
        json={
            "inn": "7707083893",
            "organization_name": 'ООО "Тест"',
            "applicant_full_name": "Алексеев Денис",
            "applicant_snils": "112-233-445 00",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("SNILS" in str(err) for err in data["detail"])


@pytest.mark.asyncio
async def test_status_lifecycle_flow(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/requests",
        json={
            "inn": "7707083893",
            "organization_name": 'ПАО "Сбербанк"',
            "applicant_full_name": "Смирнов Сергей",
            "applicant_snils": "112-233-445 95",
        },
    )
    assert create_res.status_code == 201
    request_id = create_res.json()["id"]

    res = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "SUBMITTED", "changed_by": "portal"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    res = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={
            "status": "REJECTED",
            "rejection_reason": "Неполный пакет документов",
            "changed_by": "verifier",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"
    assert res.json()["rejection_reason"] == "Неполный пакет документов"

    res = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "DRAFT", "comment": "Догружены недостающие файлы"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "DRAFT"

    await client.patch(f"/api/v1/requests/{request_id}/status", json={"status": "SUBMITTED"})
    res = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "APPROVED", "changed_by": "supervisor"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    detail = await client.get(f"/api/v1/requests/{request_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "APPROVED"
    assert len(detail.json()["status_history"]) == 5


@pytest.mark.asyncio
async def test_invalid_status_transition_conflict(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/requests",
        json={
            "inn": "7707083893",
            "organization_name": 'ПАО "Сбербанк"',
            "applicant_full_name": "Кузнецов Андрей",
            "applicant_snils": "112-233-445 95",
        },
    )
    assert create_res.status_code == 201
    request_id = create_res.json()["id"]

    # DRAFT -> APPROVED (запрещено)
    res = await client.patch(f"/api/v1/requests/{request_id}/status", json={"status": "APPROVED"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    await client.patch(f"/api/v1/requests/{request_id}/status", json={"status": "SUBMITTED"})

    # SUBMITTED -> REJECTED без причины (запрещено)
    res = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "REJECTED", "rejection_reason": ""},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    await client.patch(f"/api/v1/requests/{request_id}/status", json={"status": "APPROVED"})

    # APPROVED -> DRAFT (терминальный статус, переходы запрещены)
    res = await client.patch(f"/api/v1/requests/{request_id}/status", json={"status": "DRAFT"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

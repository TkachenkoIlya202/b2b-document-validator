from collections.abc import Sequence
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_database_session, get_request_service
from app.models.certificate_request import RequestStatus
from app.schemas.request import (
    CertificateRequestCreate,
    CertificateRequestDetailResponse,
    CertificateRequestResponse,
    CertificateRequestStatusUpdate,
)
from app.services.request_service import RequestService

router = APIRouter()


@router.post(
    "",
    response_model=CertificateRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    payload: CertificateRequestCreate,
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_database_session),
    service: RequestService = Depends(get_request_service),
):
    return await service.create_request(session, payload, x_idempotency_key)


@router.patch(
    "/{id}/status",
    response_model=CertificateRequestResponse,
    status_code=status.HTTP_200_OK,
)
async def update_request_status(
    id: int,
    payload: CertificateRequestStatusUpdate,
    session: AsyncSession = Depends(get_database_session),
    service: RequestService = Depends(get_request_service),
):
    return await service.change_status(session, id, payload)


@router.get(
    "/{id}",
    response_model=CertificateRequestDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_request(
    id: int,
    session: AsyncSession = Depends(get_database_session),
    service: RequestService = Depends(get_request_service),
):
    return await service.get_request_by_id(session, id)


@router.get(
    "",
    response_model=list[CertificateRequestResponse],
    status_code=status.HTTP_200_OK,
)
async def list_requests(
    status_filter: RequestStatus | None = Query(None, alias="status"),
    inn_filter: str | None = Query(None, alias="inn"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_database_session),
    service: RequestService = Depends(get_request_service),
):
    return await service.list_requests(
        session=session,
        status_filter=status_filter,
        inn_filter=inn_filter,
        limit=limit,
        offset=offset,
    )

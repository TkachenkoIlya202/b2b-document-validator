from collections.abc import Sequence
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BusinessException,
    EntityNotFoundException,
    ErrorCode,
    InvalidStatusTransitionException,
)
from app.models.certificate_request import (
    CertificateRequest,
    RequestStatus,
    RequestStatusHistory,
)
from app.models.organization import Organization
from app.schemas.request import (
    CertificateRequestCreate,
    CertificateRequestStatusUpdate,
)

ALLOWED_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.DRAFT: {RequestStatus.SUBMITTED},
    RequestStatus.SUBMITTED: {RequestStatus.APPROVED, RequestStatus.REJECTED},
    RequestStatus.REJECTED: {RequestStatus.DRAFT},
    RequestStatus.APPROVED: set(),
}


class RequestService:
    async def get_or_create_organization(
        self,
        session: AsyncSession,
        inn: str,
        name: str,
        kpp: str | None = None,
    ) -> Organization:
        stmt = select(Organization).where(Organization.inn == inn)
        org = (await session.execute(stmt)).scalar_one_or_none()

        if not org:
            org = Organization(inn=inn, name=name, kpp=kpp)
            session.add(org)
            await session.flush()
        elif kpp and org.kpp != kpp:
            org.kpp = kpp
            await session.flush()

        return org

    async def create_request(
        self,
        session: AsyncSession,
        data: CertificateRequestCreate,
        idempotency_key: str | None = None,
    ) -> CertificateRequest:
        if idempotency_key:
            stmt = (
                select(CertificateRequest)
                .options(selectinload(CertificateRequest.organization))
                .where(CertificateRequest.idempotency_key == idempotency_key)
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                return existing

        org = await self.get_or_create_organization(
            session=session,
            inn=data.inn,
            name=data.organization_name,
            kpp=data.kpp,
        )

        request = CertificateRequest(
            org_id=org.id,
            applicant_full_name=data.applicant_full_name,
            applicant_snils=data.applicant_snils,
            status=RequestStatus.DRAFT,
            idempotency_key=idempotency_key,
        )
        session.add(request)
        await session.flush()
        await session.refresh(request, ["organization"])
        return request

    async def change_status(
        self,
        session: AsyncSession,
        request_id: int,
        update_data: CertificateRequestStatusUpdate,
    ) -> CertificateRequest:
        stmt = (
            select(CertificateRequest)
            .options(selectinload(CertificateRequest.organization))
            .where(CertificateRequest.id == request_id)
        )
        request = (await session.execute(stmt)).scalar_one_or_none()
        if not request:
            raise EntityNotFoundException("CertificateRequest", request_id)

        current_status = request.status
        target_status = update_data.status

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStatusTransitionException(
                current_status=current_status.value,
                target_status=target_status.value,
                message=(
                    f"Transition from {current_status.value} to {target_status.value} is not allowed. "
                    f"Allowed target statuses: {[s.value for s in allowed]}"
                ),
            )

        if target_status == RequestStatus.REJECTED:
            if not update_data.rejection_reason or not update_data.rejection_reason.strip():
                raise BusinessException(
                    message="Rejection reason is required when rejecting a request",
                    error_code=ErrorCode.INVALID_STATUS_TRANSITION,
                    status_code=status.HTTP_409_CONFLICT,
                    details={"current_status": current_status.value, "target_status": target_status.value},
                )

        history_entry = RequestStatusHistory(
            request_id=request.id,
            old_status=current_status,
            new_status=target_status,
            changed_by=update_data.changed_by,
            comment=update_data.comment,
        )
        session.add(history_entry)

        request.status = target_status
        request.rejection_reason = (
            update_data.rejection_reason.strip() if target_status == RequestStatus.REJECTED else None
        )

        await session.flush()
        await session.refresh(request, ["organization"])
        return request

    async def get_request_by_id(
        self,
        session: AsyncSession,
        request_id: int,
    ) -> CertificateRequest:
        stmt = (
            select(CertificateRequest)
            .options(
                selectinload(CertificateRequest.organization),
                selectinload(CertificateRequest.status_history),
            )
            .where(CertificateRequest.id == request_id)
        )
        request = (await session.execute(stmt)).scalar_one_or_none()
        if not request:
            raise EntityNotFoundException("CertificateRequest", request_id)
        return request

    async def list_requests(
        self,
        session: AsyncSession,
        status_filter: RequestStatus | None = None,
        inn_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CertificateRequest]:
        query = (
            select(CertificateRequest)
            .options(selectinload(CertificateRequest.organization))
            .order_by(CertificateRequest.created_at.desc())
        )
        if status_filter is not None:
            query = query.where(CertificateRequest.status == status_filter)

        if inn_filter is not None:
            query = query.join(CertificateRequest.organization).where(Organization.inn == inn_filter.strip())

        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return result.scalars().all()

from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class RequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class CertificateRequest(Base):
    __tablename__ = "certificate_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    applicant_snils: Mapped[str] = mapped_column(String(14), nullable=False, index=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status_enum", native_enum=True),
        default=RequestStatus.DRAFT,
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(back_populates="requests")
    status_history: Mapped[list["RequestStatusHistory"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestStatusHistory.created_at",
    )


class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("certificate_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[RequestStatus | None] = mapped_column(
        Enum(RequestStatus, name="request_status_enum", native_enum=True),
        nullable=True,
    )
    new_status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status_enum", native_enum=True),
        nullable=False,
    )
    changed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    request: Mapped["CertificateRequest"] = relationship(back_populates="status_history")

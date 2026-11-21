import enum

from sqlalchemy import Enum, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    WAYBILL = "waybill"
    CONTRACT = "contract"
    CUSTOMS_DECLARATION = "customs_declaration"


class DocumentValidation(TimestampedBase):
    __tablename__ = "document_validations"

    document_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    organization_inn: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus),
        default=ValidationStatus.PENDING,
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    validation_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

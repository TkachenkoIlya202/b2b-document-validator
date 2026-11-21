from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.certificate_request import RequestStatus
from app.services.validators import validate_legal_entity_inn, validate_snils


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: RequestStatus | None = None
    new_status: RequestStatus
    changed_by: str | None = None
    comment: str | None = None
    created_at: datetime


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inn: str
    kpp: str | None = None
    name: str
    created_at: datetime


class CertificateRequestCreate(BaseModel):
    inn: str = Field(..., examples=["7707083893"])
    kpp: str | None = Field(None, max_length=9, examples=["770701001"])
    organization_name: str = Field(..., min_length=1, max_length=255, examples=['ПАО "Сбербанк"'])
    applicant_full_name: str = Field(..., min_length=1, max_length=255, examples=["Иванов Иван Иванович"])
    applicant_snils: str = Field(..., examples=["112-233-445 95"])

    @field_validator("inn")
    @classmethod
    def validate_inn_field(cls, v: str) -> str:
        return validate_legal_entity_inn(v)

    @field_validator("applicant_snils")
    @classmethod
    def validate_snils_field(cls, v: str) -> str:
        return validate_snils(v)


class CertificateRequestStatusUpdate(BaseModel):
    status: RequestStatus
    rejection_reason: str | None = Field(None, max_length=1000)
    changed_by: str | None = Field(None, max_length=100)
    comment: str | None = Field(None, max_length=1000)


class CertificateRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    applicant_full_name: str
    applicant_snils: str
    status: RequestStatus
    rejection_reason: str | None = None
    idempotency_key: str | None = None
    created_at: datetime
    updated_at: datetime
    organization: OrganizationResponse | None = None


class CertificateRequestDetailResponse(CertificateRequestResponse):
    status_history: list[StatusHistoryResponse] = Field(default_factory=list)

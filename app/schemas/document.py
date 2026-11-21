from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentType, ValidationStatus


class DocumentValidationRequest(BaseModel):
    organization_inn: str = Field(..., min_length=10, max_length=12, examples=["7707083893"])
    document_type: DocumentType = Field(..., examples=[DocumentType.INVOICE])
    payload: dict = Field(default_factory=dict)


class DocumentValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class DocumentValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_uid: str
    organization_inn: str
    document_type: DocumentType
    status: ValidationStatus
    payload: dict
    validation_errors: dict | None = None
    created_at: datetime
    updated_at: datetime

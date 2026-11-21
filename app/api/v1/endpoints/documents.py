from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_database_session, get_validator_service
from app.schemas.document import DocumentValidationRequest, DocumentValidationResponse
from app.services.validator import DocumentValidatorService

router = APIRouter()


@router.post(
    "/validate",
    response_model=DocumentValidationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def validate_document(
    request: DocumentValidationRequest,
    session: AsyncSession = Depends(get_database_session),
    service: DocumentValidatorService = Depends(get_validator_service),
):
    return await service.create_validation_request(session, request)


@router.get(
    "/{document_uid}",
    response_model=DocumentValidationResponse,
)
async def get_document_validation(
    document_uid: str,
    session: AsyncSession = Depends(get_database_session),
    service: DocumentValidatorService = Depends(get_validator_service),
):
    record = await service.get_by_uid(session, document_uid)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document validation '{document_uid}' not found",
        )
    return record

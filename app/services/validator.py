import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentType, DocumentValidation, ValidationStatus
from app.schemas.document import DocumentValidationRequest, DocumentValidationResult


class DocumentValidatorService:
    @staticmethod
    def validate_inn(inn: str) -> bool:
        return inn.isdigit() and len(inn) in (10, 12)

    @staticmethod
    def validate_payload(doc_type: DocumentType, payload: dict) -> DocumentValidationResult:
        errors = []
        if doc_type == DocumentType.INVOICE:
            for field in ("number", "date", "total_amount"):
                if field not in payload:
                    errors.append(f"Missing required invoice field: '{field}'")
        elif doc_type == DocumentType.WAYBILL:
            for field in ("waybill_number", "shipper", "consignee"):
                if field not in payload:
                    errors.append(f"Missing required waybill field: '{field}'")

        return DocumentValidationResult(is_valid=len(errors) == 0, errors=errors)

    async def create_validation_request(
        self,
        session: AsyncSession,
        request_data: DocumentValidationRequest,
    ) -> DocumentValidation:
        validation_res = self.validate_payload(request_data.document_type, request_data.payload)
        inn_valid = self.validate_inn(request_data.organization_inn)

        all_errors = list(validation_res.errors)
        if not inn_valid:
            all_errors.append("Invalid organization INN (must be 10 or 12 digits)")

        status = ValidationStatus.VALID if not all_errors else ValidationStatus.INVALID
        validation_errors = {"details": all_errors} if all_errors else None

        record = DocumentValidation(
            document_uid=str(uuid.uuid4()),
            organization_inn=request_data.organization_inn,
            document_type=request_data.document_type,
            status=status,
            payload=request_data.payload,
            validation_errors=validation_errors,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    async def get_by_uid(
        self,
        session: AsyncSession,
        document_uid: str,
    ) -> DocumentValidation | None:
        query = select(DocumentValidation).where(DocumentValidation.document_uid == document_uid)
        result = await session.execute(query)
        return result.scalar_one_or_none()

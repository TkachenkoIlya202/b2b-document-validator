from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.request_service import RequestService
from app.services.validator import DocumentValidatorService


async def get_database_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    yield session


def get_validator_service() -> DocumentValidatorService:
    return DocumentValidatorService()


def get_request_service() -> RequestService:
    return RequestService()

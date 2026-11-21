from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_database_session

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def check_health(session: AsyncSession = Depends(get_database_session)):
    try:
        await session.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
    }

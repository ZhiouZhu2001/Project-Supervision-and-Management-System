import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.models.account import Account
from app.services.export import build_export

router = APIRouter(tags=["export"])


@router.get("/export.json")
async def export_json(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Everything the owner wrote, as one downloadable document (R13)."""
    account = await db.get(Account, _account.id)
    payload: dict[str, Any] = await build_export(
        db, email=account.email if account is not None else ""
    )

    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="daymark-export.json"'},
    )

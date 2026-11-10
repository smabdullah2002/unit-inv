from typing import Optional
from uuid import UUID
from fastapi import Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import UnauthorizedError, ValidationError
from app.services.unit_service import UnitService


class BranchContext(BaseModel):
    branch_id: UUID
    user_id: Optional[UUID] = None


async def get_branch_context(
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-ID"),
    authorization: Optional[str] = Header(None),
) -> BranchContext:
    # 1. Check X-Branch-ID header
    if x_branch_id:
        try:
            branch_uuid = UUID(x_branch_id)
            return BranchContext(branch_id=branch_uuid)
        except ValueError:
            raise ValidationError(
                message="Invalid X-Branch-ID header format; must be a valid UUID.",
                code="INVALID_BRANCH_ID",
            )

    # 2. Check JWT Bearer token if provided
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        # In a full JWT setup we decode claims:
        # Here we support simple mock/token format or decode if payload is present
        # If payload contains branch_id claim:
        import base64
        import json

        try:
            parts = token.split(".")
            if len(parts) == 3:
                # Basic JWT claim inspection
                padded = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                if "branch_id" in payload:
                    return BranchContext(
                        branch_id=UUID(payload["branch_id"]),
                        user_id=UUID(payload["sub"]) if "sub" in payload else None,
                    )
        except Exception:
            pass

    raise UnauthorizedError(
        message="Branch context required. Provide 'X-Branch-ID' header or Bearer token with branch_id claim.",
        code="UNAUTHORIZED",
    )


async def get_unit_service(
    session: AsyncSession = Depends(get_session),
) -> UnitService:
    return UnitService(session=session)


from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.unit import Unit
from app.repositories.branch_repository import BranchRepository
from app.repositories.unit_repository import UnitRepository
from app.schemas.common import Page
from app.schemas.unit import UnitCreate, UnitListQuery, UnitOut, UnitUpdate


class UnitService:
    def __init__(
        self,
        session: AsyncSession,
        unit_repository: Optional[UnitRepository] = None,
        branch_repository: Optional[BranchRepository] = None,
    ):
        self.session = session
        self.unit_repo = unit_repository or UnitRepository(session)
        self.branch_repo = branch_repository or BranchRepository(session)

    async def _validate_branch(self, branch_id: UUID) -> None:
        branch = await self.branch_repo.get_by_id(branch_id)
        if not branch:
            raise NotFoundError(message="Branch not found.", code="BRANCH_NOT_FOUND")
        if not branch.is_active:
            raise ForbiddenError(message="Branch is inactive.", code="BRANCH_INACTIVE")

    async def create_unit(self, branch_id: UUID, unit_in: UnitCreate) -> UnitOut:
        await self._validate_branch(branch_id)

        if await self.unit_repo.exists_by_code(branch_id, unit_in.code):
            raise ConflictError(
                message=f"A unit with code '{unit_in.code}' already exists in this branch.",
                code="UNIT_CODE_EXISTS",
            )

        if await self.unit_repo.exists_by_name(branch_id, unit_in.name):
            raise ConflictError(
                message=f"A unit with name '{unit_in.name}' already exists in this branch.",
                code="UNIT_NAME_EXISTS",
            )

        unit = Unit(
            branch_id=branch_id,
            name=unit_in.name,
            code=unit_in.code,
            type=unit_in.type,
            is_active=unit_in.is_active,
        )

        try:
            created_unit = await self.unit_repo.create(unit)
            await self.session.commit()
            await self.session.refresh(created_unit)
            return UnitOut.model_validate(created_unit)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(
                message="A unit with this name or code already exists in this branch.",
                code="UNIT_CONFLICT",
            )

    async def get_unit(self, branch_id: UUID, unit_id: UUID) -> UnitOut:
        await self._validate_branch(branch_id)
        unit = await self.unit_repo.get_by_id(branch_id, unit_id)
        if not unit:
            raise NotFoundError(message="Unit not found.", code="UNIT_NOT_FOUND")
        return UnitOut.model_validate(unit)

    async def list_units(self, branch_id: UUID, query: UnitListQuery) -> Page[UnitOut]:
        await self._validate_branch(branch_id)
        items, total = await self.unit_repo.list(branch_id, query)
        return Page(
            items=[UnitOut.model_validate(item) for item in items],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def update_unit(
        self, branch_id: UUID, unit_id: UUID, unit_in: UnitUpdate
    ) -> UnitOut:
        await self._validate_branch(branch_id)
        unit = await self.unit_repo.get_by_id(branch_id, unit_id)
        if not unit:
            raise NotFoundError(message="Unit not found.", code="UNIT_NOT_FOUND")

        if unit_in.code is not None and unit_in.code != unit.code:
            if await self.unit_repo.exists_by_code(branch_id, unit_in.code, exclude_id=unit_id):
                raise ConflictError(
                    message=f"A unit with code '{unit_in.code}' already exists in this branch.",
                    code="UNIT_CODE_EXISTS",
                )
            unit.code = unit_in.code

        if unit_in.name is not None and unit_in.name != unit.name:
            if await self.unit_repo.exists_by_name(branch_id, unit_in.name, exclude_id=unit_id):
                raise ConflictError(
                    message=f"A unit with name '{unit_in.name}' already exists in this branch.",
                    code="UNIT_NAME_EXISTS",
                )
            unit.name = unit_in.name

        if unit_in.type is not None:
            unit.type = unit_in.type

        if unit_in.is_active is not None:
            unit.is_active = unit_in.is_active

        unit.updated_at = datetime.now(timezone.utc)

        try:
            updated_unit = await self.unit_repo.update(unit)
            await self.session.commit()
            await self.session.refresh(updated_unit)
            return UnitOut.model_validate(updated_unit)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(
                message="A unit with this name or code already exists in this branch.",
                code="UNIT_CONFLICT",
            )

    async def delete_unit(self, branch_id: UUID, unit_id: UUID) -> None:
        await self._validate_branch(branch_id)
        unit = await self.unit_repo.get_by_id(branch_id, unit_id)
        if not unit:
            raise NotFoundError(message="Unit not found.", code="UNIT_NOT_FOUND")

        await self.unit_repo.soft_delete(branch_id, unit_id)
        await self.session.commit()


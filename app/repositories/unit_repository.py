from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unit import Unit
from app.repositories.base import BaseRepository
from app.schemas.unit import UnitListQuery


class UnitRepository(BaseRepository[Unit]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def exists_by_code(
        self, branch_id: UUID, code: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        stmt = select(func.count(Unit.id)).where(
            Unit.branch_id == branch_id,
            Unit.code == code,
            Unit.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Unit.id != exclude_id)
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def exists_by_name(
        self, branch_id: UUID, name: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        stmt = select(func.count(Unit.id)).where(
            Unit.branch_id == branch_id,
            Unit.name == name,
            Unit.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Unit.id != exclude_id)
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def create(self, unit: Unit) -> Unit:
        self.session.add(unit)
        await self.session.flush()
        return unit

    async def get_by_id(self, branch_id: UUID, unit_id: UUID) -> Optional[Unit]:
        stmt = select(Unit).where(
            Unit.branch_id == branch_id,
            Unit.id == unit_id,
            Unit.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, branch_id: UUID, query: UnitListQuery
    ) -> Tuple[List[Unit], int]:
        filters = [
            Unit.branch_id == branch_id,
            Unit.deleted_at.is_(None),
        ]

        if query.type is not None:
            filters.append(Unit.type == query.type)

        if query.is_active is not None:
            filters.append(Unit.is_active == query.is_active)

        if query.search:
            search_pattern = f"%{query.search.strip()}%"
            filters.append(
                or_(
                    Unit.name.ilike(search_pattern),
                    Unit.code.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count(Unit.id)).where(*filters)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sort
        sort_column = getattr(Unit, query.sort_by, Unit.name)
        if query.order == "desc":
            order_clause = sort_column.desc()
        else:
            order_clause = sort_column.asc()

        offset = (query.page - 1) * query.page_size
        items_stmt = (
            select(Unit)
            .where(*filters)
            .order_by(order_clause)
            .offset(offset)
            .limit(query.page_size)
        )
        items_res = await self.session.execute(items_stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def update(self, unit: Unit) -> Unit:
        await self.session.flush()
        return unit

    async def soft_delete(self, branch_id: UUID, unit_id: UUID) -> Optional[Unit]:
        unit = await self.get_by_id(branch_id, unit_id)
        if not unit:
            return None
        unit.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return unit


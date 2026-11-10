from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.repositories.base import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, branch_id: UUID) -> Optional[Branch]:
        stmt = select(Branch).where(Branch.id == branch_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, branch: Branch) -> Branch:
        self.session.add(branch)
        await self.session.flush()
        return branch


import asyncio
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.branch import Branch
from app.models.unit import Unit, UnitType
from app.repositories.branch_repository import BranchRepository
from app.repositories.unit_repository import UnitRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEFAULT_BRANCH_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        branch_repo = BranchRepository(session)
        unit_repo = UnitRepository(session)

        # 1. Create or get default branch
        branch = await branch_repo.get_by_id(DEFAULT_BRANCH_ID)
        if not branch:
            branch = Branch(
                id=DEFAULT_BRANCH_ID,
                name="Headquarters Branch",
                is_active=True,
            )
            await branch_repo.create(branch)
            logger.info(f"Created default branch: {branch.name} ({branch.id})")
        else:
            logger.info(f"Default branch already exists: {branch.name} ({branch.id})")

        # 2. Seed standard units
        standard_units = [
            ("Kilogram", "kg", UnitType.weight),
            ("Gram", "g", UnitType.weight),
            ("Litre", "l", UnitType.volume),
            ("Millilitre", "ml", UnitType.volume),
            ("Piece", "pc", UnitType.count),
            ("Box", "bx", UnitType.count),
        ]

        for name, code, u_type in standard_units:
            exists = await unit_repo.exists_by_code(branch.id, code)
            if not exists:
                unit = Unit(
                    id=uuid.uuid4(),
                    branch_id=branch.id,
                    name=name,
                    code=code,
                    type=u_type,
                    is_active=True,
                )
                await unit_repo.create(unit)
                logger.info(f"Seeded unit: {name} [{code}]")
            else:
                logger.info(f"Unit already exists: {name} [{code}]")

        await session.commit()
    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed())


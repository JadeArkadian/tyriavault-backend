from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.database.repositories.base_repository import BaseRepository
from app.database.repositories.genders_repository import GendersRepository
from app.database.repositories.item_types_repo import ItemTypesRepository
from app.database.repositories.races_repository import RacesRepository
from app.database.repositories.rarities_repository import RaritiesRepository
from app.database.seeding.seed_data import GENDERS_DATA, RACES_DATA, RARITIES_DATA, ITEM_TYPES_DATA


class DatabaseSeeder:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gender_repo = GendersRepository(session)
        self.race_repo = RacesRepository(session)
        self.rarity_repo = RaritiesRepository(session)
        self.item_type_repo = ItemTypesRepository(session)

    async def seed_all(self) -> None:
        """Seed all necessary data into the database."""

        try:
            await self.upsert_data(self.gender_repo, GENDERS_DATA)
            await self.upsert_data(self.race_repo, RACES_DATA)
            await self.upsert_data(self.rarity_repo, RARITIES_DATA)
            await self.upsert_data(self.item_type_repo, ITEM_TYPES_DATA)

            await self.session.commit()
            logger.info("Database seeding completed successfully")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error seeding database: {e}")
            raise

    async def upsert_data(self, repo: BaseRepository, data: list) -> None:
        """Upsert data using the provided repository."""

        logger.info(f"Seeding data for {repo.__class__.__name__}...")
        await repo.upsert_batch(data)

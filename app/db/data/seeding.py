from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.data.genders_data import GENDERS_DATA
from app.db.data.professions_data import PROFESSIONS_DATA
from app.db.data.races_data import RACES_DATA
from app.db.model import Genders, Races, Professions


async def seed_data(db: AsyncSession):
    """
    Seeds the database with initial data for Genders, Races and Professions.
    Updates existing entries if they differ from the seed data.
    """
    try:
        # Seed Genders
        logger.info("Seeding Genders...")
        for gender_data in GENDERS_DATA:
            result = await db.execute(select(Genders).filter_by(id=gender_data["id"]))
            gender = result.scalar_one_or_none()
            if gender:
                # Update if exists
                gender.name_en = gender_data["name_en"]
                gender.name_es = gender_data["name_es"]
                gender.name_de = gender_data["name_de"]
                gender.name_fr = gender_data["name_fr"]
            else:
                # Insert if not exists
                db.add(Genders(**gender_data))

        # Seed Races
        logger.info("Seeding Races...")
        for race_data in RACES_DATA:
            result = await db.execute(select(Races).filter_by(id=race_data["id"]))
            race = result.scalar_one_or_none()
            if race:
                # Update if exists
                race.name_en = race_data["name_en"]
                race.name_es = race_data["name_es"]
                race.name_de = race_data["name_de"]
                race.name_fr = race_data["name_fr"]
            else:
                # Insert if not exists
                db.add(Races(**race_data))

        # Seed Professions
        logger.info("Seeding Professions...")
        for prof_data in PROFESSIONS_DATA:
            result = await db.execute(select(Professions).filter_by(id=prof_data["id"]))
            profession = result.scalar_one_or_none()
            if profession:
                # Update if exists
                profession.name_en = prof_data["name_en"]
                profession.name_es = prof_data["name_es"]
                profession.name_de = prof_data["name_de"]
                profession.name_fr = prof_data["name_fr"]
            else:
                # Insert if not exists
                db.add(Professions(**prof_data))

        await db.commit()
    finally:
        await db.close()

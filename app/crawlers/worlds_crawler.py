from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.worlds import get_worlds_info_from_api
from app.core.logging import logger
from app.db.model import Worlds
from app.gw2.client import GW2Client


async def update_worlds_incremental(db: AsyncSession):
    gw2 = GW2Client()
    logger.info("Start updating worlds incremental")

    # Query worlds from GW2 API
    worlds_info_from_api = await get_worlds_info_from_api(gw2)
    if not worlds_info_from_api:
        return

    # Check existing worlds in DB
    result = await db.execute(select(Worlds))
    worlds_db = {w.id: w for w in result.scalars().all()}

    # Update or insert worlds as necessary
    for world in worlds_info_from_api:
        world_id = world["id"]
        names = {
            "name_es": world.get("name_es", ""),
            "name_fr": world.get("name_fr", ""),
            "name_en": world.get("name_en", ""),
            "name_de": world.get("name_de", "")
        }
        if world_id in worlds_db:
            db_world = worlds_db[world_id]
            # If any name has changed, update the record
            if any(getattr(db_world, k) != v for k, v in names.items()):
                logger.debug(f"Updating world: {world_id}")
                await db.execute(
                    update(Worlds)
                    .where(Worlds.id == world_id)
                    .values(**names)
                )
        else:
            # Insert new world
            logger.debug(f"inserting new world: {world_id}")
            db.add(Worlds(id=world_id, **names))
    await db.commit()
    logger.info("End updating worlds incremental")

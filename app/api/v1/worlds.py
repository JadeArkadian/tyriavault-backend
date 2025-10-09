import asyncio

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db
from app.db.model import Worlds
from app.gw2.client import GW2Client

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("/", summary="Provides info about worlds", response_description="Worlds info")
async def get_worlds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Worlds))
    worlds_info = result.scalars().all()

    # No worlds on DB? -> check if the token is valid with GW2 API
    if worlds_info is None or not worlds_info:
        gw2 = GW2Client()
        worlds_info_from_api = await _get_worlds_info_from_api(gw2)
        if worlds_info_from_api is not None:
            # Store the worlds in the database
            for world in worlds_info_from_api:
                db.add(Worlds(**world))
            await db.commit()
            worlds_info = worlds_info_from_api

    return worlds_info


async def _get_worlds_info_from_api(gw2: GW2Client):
    try:
        results = await asyncio.gather(
            gw2.get_worlds(lang="en"),
            gw2.get_worlds(lang="es"),
            gw2.get_worlds(lang="de"),
            gw2.get_worlds(lang="fr")
        )

        combined_worlds = {}

        for lang, worlds in zip(["en", "es", "de", "fr"], results):
            for world in worlds:
                world_id = world["id"]
                if world_id not in combined_worlds:
                    combined_worlds[world_id] = {"id": world_id}
                combined_worlds[world_id][f"name_{lang}"] = world["name"]

        return list(combined_worlds.values())

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Conection failure: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

import asyncio

from fastapi import APIRouter
from fastapi_cache.decorator import cache

from app.api.v1.responses.worlds_reponse import WorldsResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.core.utils import handle_gw2_api_error
from app.gw2.client import GW2Client

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("/", summary="Provides info about worlds", response_description="Worlds info")
@cache(expire=settings.CACHE_TTL_SECONDS, namespace="worlds", key_builder=cache_key_builder)
async def get_worlds() -> list[WorldsResponse]:
    gw2 = GW2Client()
    worlds_info_from_api = await get_worlds_info_from_api(gw2)
    return [WorldsResponse.map_response(world) for world in worlds_info_from_api]


async def get_worlds_info_from_api(gw2: GW2Client) -> list[dict]:
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
    except Exception as e:
        handle_gw2_api_error(e)

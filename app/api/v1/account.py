from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.responses.account_responses import AccountInfoResponse
from app.core.utils import split_bearer_token
from app.db.dependency import get_db
from app.db.model import GameAccounts, ApiKeys
from app.gw2.client import GW2Client

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/", summary="Account summary", response_description="Account details")
async def account_details(
        authorization: str = Header(..., description="Authorization header: Bearer <API_KEY>"),
        db: AsyncSession = Depends(get_db)) -> AccountInfoResponse:
    try:
        token = split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # First we look in the DB if we have an account associated with this token
    result = await db.execute(
        select(GameAccounts)
        .options(selectinload(GameAccounts.world))
        .join(ApiKeys, GameAccounts.uuid == ApiKeys.game_account_uuid)
        .filter(ApiKeys.api_key == token)
    )
    game_account = result.scalars().first()

    # No account found in DB -> Lets check with GW2 API
    if game_account is None:
        gw2 = GW2Client(api_key=token)
        game_account_info_from_api = await _get_account_info_from_api(gw2)
        if game_account_info_from_api:
            # Store the valid account in the database
            new_game_account = GameAccounts(
                account_name=game_account_info_from_api.get("name"),
                creation_date=game_account_info_from_api.get("created"),
                fractal_level=game_account_info_from_api.get("fractal_level"),
                uuid=game_account_info_from_api.get("id"),
                world_id=game_account_info_from_api.get("world"),
                content_access=game_account_info_from_api.get("access")
            )

            db.add(new_game_account)
            await db.commit()
            await db.refresh(new_game_account)
            game_account = new_game_account

            # Update the API key to link with this account
            api_key_obj = await db.execute(
                select(ApiKeys).filter(ApiKeys.api_key == token)
            )
            api_key_instance = api_key_obj.scalars().first()
            if api_key_instance:
                api_key_instance.game_account_uuid = new_game_account.uuid
                api_key_instance.last_time_checked = datetime.now()
                db.add(api_key_instance)
                await db.commit()
                await db.refresh(api_key_instance)

    return AccountInfoResponse.map_response(game_account)


async def _get_account_info_from_api(gw2: GW2Client):
    try:
        return await gw2.get_account()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Missing or invalid token.")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="Missing or unauthorized token.")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Conection failure: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

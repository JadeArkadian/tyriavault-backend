import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import split_bearer_token
from app.db.dependency import get_db
from app.db.model import GameAccounts, ApiKeys
from app.gw2.client import GW2Client

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/", summary="Account summary", response_description="Account details")
async def account_details(
        authorization: str = Header(..., description="Authorization header: Bearer <API_KEY>"),
        db: AsyncSession = Depends(get_db)):
    try:
        token = split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # First we look in the DB if we have an account associated with this token
    result = await db.execute(
        select(GameAccounts)
        .join(ApiKeys, GameAccounts.id == ApiKeys.game_account_id)
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
                world=game_account_info_from_api.get("world"),
                creation_date=game_account_info_from_api.get("created"),
                fractal_level=game_account_info_from_api.get("fractal_level"),
                last_modified=game_account_info_from_api.get("last_modified"),
            )

            db.add(new_game_account)
            await db.commit()
            await db.refresh(new_game_account)
            game_account = new_game_account

    return game_account


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

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.currencies import get_currencies_info_from_api
from app.core.logging import logger
from app.db.model import Currencies
from app.gw2.client import GW2Client


async def update_currencies_incremental(db: AsyncSession):
    gw2 = GW2Client()
    logger.info("Start updating currencies incremental")

    # Query currencies from GW2 API
    currencies_info_from_api = await get_currencies_info_from_api(gw2)
    if not currencies_info_from_api:
        return

    # Check existing currencies in DB
    result = await db.execute(select(Currencies))
    currencies_db = {c.id: c for c in result.scalars().all()}

    # Update or insert currencies as necessary
    for currency in currencies_info_from_api:
        currency_id = currency["id"]
        values = {
            "name_es": currency.get("name_es", ""),
            "name_fr": currency.get("name_fr", ""),
            "name_en": currency.get("name_en", ""),
            "name_de": currency.get("name_de", ""),
            "icon_url": currency.get("icon_url", ""),
            "description_es": currency.get("description_es", ""),
            "description_fr": currency.get("description_fr", ""),
            "description_en": currency.get("description_en", ""),
            "description_de": currency.get("description_de", "")
        }
        if currency_id in currencies_db:
            db_currency = currencies_db[currency_id]
            # If any name has changed, update the record
            if any(getattr(db_currency, k) != v for k, v in values.items()):
                logger.debug(f"Updating currency: {db_currency}")
                await db.execute(
                    update(Currencies)
                    .where(Currencies.id == currency_id)
                    .values(**values)
                )
        else:
            # Insert new currencies
            logger.debug(f"inserting new currency: {currency_id}")
            db.add(Currencies(id=currency_id, **values))
    await db.commit()
    logger.info("End updating currencies incremental")

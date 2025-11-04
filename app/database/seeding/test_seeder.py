from unittest.mock import AsyncMock, patch

import pytest

from app.database.seeding.seeder import DatabaseSeeder


@pytest.mark.asyncio
async def test_seed_all_success():
    session = AsyncMock()
    gender_repo = AsyncMock()
    race_repo = AsyncMock()
    rarity_repo = AsyncMock()

    with patch('app.database.seeding.seeder.GendersRepository', return_value=gender_repo), \
            patch('app.database.seeding.seeder.RacesRepository', return_value=race_repo), \
            patch('app.database.seeding.seeder.RaritiesRepository', return_value=rarity_repo):
        seeder = DatabaseSeeder(session)
        seeder.upsert_data = AsyncMock()
        await seeder.seed_all()
        assert seeder.upsert_data.await_count == 3
        session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_all_exception_rolls_back():
    session = AsyncMock()
    gender_repo = AsyncMock()
    race_repo = AsyncMock()
    rarity_repo = AsyncMock()

    with patch('app.database.seeding.seeder.GendersRepository', return_value=gender_repo), \
            patch('app.database.seeding.seeder.RacesRepository', return_value=race_repo), \
            patch('app.database.seeding.seeder.RaritiesRepository', return_value=rarity_repo):
        seeder = DatabaseSeeder(session)
        seeder.upsert_data = AsyncMock(side_effect=Exception('fail'))
        with pytest.raises(Exception):
            await seeder.seed_all()
        session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_data_calls_repo():
    repo = AsyncMock()
    data = [1, 2, 3]
    seeder = DatabaseSeeder(AsyncMock())
    await seeder.upsert_data(repo, data)
    repo.upsert_batch.assert_awaited_once_with(data)

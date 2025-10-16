from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.db.model import ApiKeys
from app.main import api


@pytest.mark.asyncio
async def test_tokeninfo_cache_hits_and_misses():
    mock_db = AsyncMock()

    # First execution: token not in DB (cache miss)
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result_empty
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    token = "TEST_TOKEN_123"
    gw2_token_info = {"permissions": ["account", "characters"]}

    async def _override_get_db():
        yield mock_db

    api.dependency_overrides = {}
    # Override get_db dependency to use our mock_db
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=api)

    with patch("app.core.utils.split_bearer_token", return_value=token), \
            patch("app.gw2.client.get_gw2_http_client", return_value=MagicMock()), \
            patch("app.gw2.client.GW2Client.token_info",
                  new=AsyncMock(return_value=gw2_token_info)) as mocked_token_info:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp1 = await ac.get("/api/v1/common/tokeninfo", headers={"Authorization": f"Bearer {token}"})
            assert resp1.status_code == 200
            data1 = resp1.json()
            assert data1["api_key"] == token
            assert set(data1["permissions"]) == set(gw2_token_info["permissions"])

            # We adjust the mock to return the newly created ApiKey on subsequent DB queries
            mock_api_key = ApiKeys(api_key=token, permissions=gw2_token_info["permissions"], game_account_uuid=None)
            mock_result_with_token = MagicMock()
            mock_result_with_token.scalars.return_value.first.return_value = mock_api_key
            mock_db.execute.return_value = mock_result_with_token

            # Second execution: token now in DB (cache hit)
            resp2 = await ac.get("/api/v1/common/tokeninfo", headers={"Authorization": f"Bearer {token}"})
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert data2 == data1  # respuesta proviene de caché

    # Asserts
    # token_info only called once (the first time, cache miss)
    assert mocked_token_info.call_count == 1
    assert mock_db.execute.call_count == 1
    # commit and refresh called only once when inserting new ApiKey
    assert mock_db.commit.call_count == 1
    assert mock_db.refresh.call_count == 1

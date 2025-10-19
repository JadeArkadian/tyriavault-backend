from app.api.v1.responses.common_responses import TokenInfoResponse
from app.db.model import ApiKeys


def map_apikeys_to_tokeninforesponse(api_key: ApiKeys) -> TokenInfoResponse:
    return TokenInfoResponse(
        api_key=api_key.api_key,
        permissions=api_key.permissions,
        last_time_checked=api_key.last_time_checked,
        game_account_uuid=api_key.game_account_uuid
    )

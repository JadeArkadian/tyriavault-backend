from fastapi import APIRouter, Response

router = APIRouter(prefix="/account", tags=["account"])

@router.get("/", summary="Account summary", response_description="Account details")
def account_details():
    """
    Account details endpoint to verify account information.
    :return:
    - 200 OK with "alive" message if the service is running.
    - 500 Internal Server Error if the service is down.
    """
    return Response(content="alive", media_type="text/plain", status_code=200)
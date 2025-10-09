from fastapi import APIRouter, Response

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", summary="Returns cached items", response_description="Cached Items")
def items_cached_list():
    """
    Returns al cached items
    :return:
    - 200 OK with "alive" message if the service is running.
    - 500 Internal Server Error if the service is down.
    """
    return Response(content="alive", media_type="text/plain", status_code=200)

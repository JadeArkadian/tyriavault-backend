from fastapi import APIRouter, Response

router = APIRouter(prefix="/common", tags=["common"])

@router.get("/status", summary="Health Check", response_description="Service is alive")
def status():
    """
    Health check endpoint to verify if the service is running.
    :return:
    - 200 OK with "alive" message if the service is running.
    - 500 Internal Server Error if the service is down.
    """
    return Response(content="alive", media_type="text/plain", status_code=200)
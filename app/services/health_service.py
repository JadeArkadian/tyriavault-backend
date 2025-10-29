from app.gw2.client import GW2Client


class HealthService:
    """
    Service to check the health status of external dependencies like GW2 API.
    """

    def __init__(self, gw2_client: GW2Client):
        self.gw2_client = gw2_client

    async def check_gw2_api_status(self) -> bool:
        """
        Check if the GW2 API is responding correctly.
        Returns True if the API is up, False otherwise.
        """
        try:
            await self.gw2_client.get_build()
            return True
        except Exception:
            return False

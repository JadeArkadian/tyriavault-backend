from fastapi.testclient import TestClient

from app.main import api

client = TestClient(api)


class TestAPICommon:
    def test_notfound_service(self):
        response = client.get("/api/v1/common/")
        assert response.status_code == 404

    def test_status_alive(self):
        response = client.get("/api/v1/common/status")
        assert response.status_code == 200
        assert response.content == b"alive"
